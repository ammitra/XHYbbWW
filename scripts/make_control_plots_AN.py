'''
Make control plots of data and MC templates per-year for data and MC 
'''

import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplhep as hep
from collections import OrderedDict
import array
import subprocess

# Options for plotting
stack_style = {
    'edgecolor': (0, 0, 0, 0.5),
}
errorbar_style = {
    'linestyle': 'none',
    'marker': '.',      # display a dot for the datapoint
    'elinewidth': 2,    # width of the errorbar line
    'markersize': 10,   # size of the error marker
    'capsize': 0,       # size of the caps on the errorbar (0: no cap fr)
    'color': 'k',       # black 
}

# Function stolen from https://root-forum.cern.ch/t/trying-to-convert-rdf-generated-histogram-into-numpy-array/53428/3
def hist2array(hist, include_overflow=False, return_errors=False):
    '''Create a numpy array from a ROOT histogram without external tools like root_numpy.

    Args:
        hist (TH1): Input ROOT histogram
        include_overflow (bool, optional): Whether or not to include the under/overflow bins. Defaults to False. 
        return_errs (bool, optional): Whether or not to return an array containing the sum of the weights squared. Defaults to False.

    Returns:
        arr (np.ndarray): Array representing the ROOT histogram
        errors (np.ndarray): Array containing the sqrt of the sum of weights squared
    '''
    hist.BufferEmpty()
    root_arr = hist.GetArray()
    if isinstance(hist, ROOT.TH1):
        shape = (hist.GetNbinsX() + 2,)
    elif isinstance(hist, ROOT.TH2):
        shape = (hist.GetNbinsY() + 2, hist.GetNbinsX() + 2)
    elif isinstance(hist, ROOT.TH3):
        shape = (hist.GetNbinsZ() + 2, hist.GetNbinsY() + 2, hist.GetNbinsX() + 2)
    else:
        raise TypeError(f'hist must be an instance of ROOT.TH1, ROOT.TH2, or ROOT.TH3')

    # Get the array and, optionally, errors
    arr = np.ndarray(shape, dtype=np.float64, buffer=root_arr, order='C')
    if return_errors:
        errors = np.sqrt(np.ndarray(shape, dtype='f8', buffer=hist.GetSumw2().GetArray()))

    if not include_overflow:
        arr = arr[tuple([slice(1, -1) for idim in range(arr.ndim)])]
        if return_errors:
            errors = errors[tuple([slice(1, -1) for idim in range(errors.ndim)])]

    if return_errors:
        return arr, errors
    else:
        return arr


def poisson_conf_interval(k):
    """
    Calculate Poisson (Garwood) confidence intervals using ROOT's TH1 with kPoisson error option.
    
    Parameters:
    k (array): The number of counts (events) per bin.

    Returns:
    lower (array): Bin count - lower error.
    upper (array): Bin count + upper error.
    """
    lower = np.zeros_like(k, dtype=float)
    upper = np.zeros_like(k, dtype=float)
    #Temp hist to exploit ROOT's built-in CI calculating function
    hist = ROOT.TH1F("hist_delete", "", 1, 0, 1)
    hist.SetBinErrorOption(ROOT.TH1.kPoisson)
    hist.Sumw2()

    for i, count in enumerate(k):
        hist.SetBinContent(1, count)
        
        lower[i] = hist.GetBinContent(1) - hist.GetBinErrorLow(1)
        upper[i] = hist.GetBinContent(1) + hist.GetBinErrorUp(1)
        
    hist.Delete()
    
    return lower, upper    

def plot_stack(
    outname,
    data = None, # numpy array
    bkgs = {},  # {latex name : (numpy array, color)} ordered by yield - use OrderedDict
    sigs = {},  # {latex name : (numpy array, color)}
    edges = None,
    title = '',
    xtitle = '',
    subtitle = '',
    totalBkg = None,
    logyFlag = False,
    plot_ratio = False,
    lumiText = r'$138 fb^{-1} (13 TeV)$',
    extraText = 'Preliminary',
    units='GeV'):

    if not plot_ratio:
        plt.style.use([hep.style.CMS])
        fig, ax = plt.subplots()
    else:
        fig, (ax, rax) = plt.subplots(
            2, 1, dpi=200, figsize=(12,14), gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05}, sharex=True
        )

    # obtain background and signals
    bkg_stack = np.vstack([val[0] for key, val in bkgs.items()])
    bkg_stack = np.hstack([bkg_stack, bkg_stack[:,-1:]])
    bkg_stack = np.hstack([bkg_stack])
    bkg_colors = [val[1] for key, val in bkgs.items()]
    bkg_labels = [key for key, val in bkgs.items()]

    sig_stack = np.vstack([val[0] for key, val in sigs.items()])
    sig_stack = np.hstack([sig_stack, sig_stack[:,-1:]])
    sig_stack = np.hstack([sig_stack])
    sig_colors = [val[1] for key, val in sigs.items()]
    sig_labels = [key for key, val in sigs.items()]

    ax.stackplot(edges, bkg_stack, labels=bkg_labels, colors=bkg_colors, step='post', **stack_style)
    width = edges[1]-edges[0]
    if 'vsQCD' in outname: units = ''
    ax.set_ylabel(f'Events')
    if plot_ratio:
        rax.set_xlabel(xtitle)
    else:
        ax.set_xlabel(xtitle)
   
    # only plot data for preselection 
    if ('preselection' in outname): 
        lower_errors, upper_errors = poisson_conf_interval(data)
        yerr = [data - lower_errors, upper_errors - data]
        bin_centers = (edges[:-1] + edges[1:])/2
        ax.errorbar(x=bin_centers, y=data, yerr=yerr, xerr=None, label='Data', **errorbar_style)

 

    # plot signals
    for key,val in sigs.items():
        sigarr = val[0]
        scaling = (totalBkg.max()/sigarr.max())
        ax.step(x=edges, y=np.hstack([sigarr,sigarr[-1]])*scaling, where='post', color=val[1], label=r'%s $\times$ %s'%(key,round(scaling,1)))
    
    if logyFlag:
        if ('preselection' in outname):
            if totalBkg.max() >= data.max():
                ax.set_ylim(0.01, totalBkg.max()*1e10)
            else:
                ax.set_ylim(0.01, data.max()*1e10)
        else:
            ax.set_ylim(0.01, totalBkg.max()*1e10)
        ax.set_yscale('log')
    else:
        if ('preselection' in outname):
            if totalBkg.max() >= data.max():
                ax.set_ylim(0, totalBkg.max()*1.5)
            else:
                ax.set_ylim(0, data.max()*1.5)
        else:
            ax.set_ylim(0, totalBkg.max()*1.5)

    ax.legend()
    if ('preselection' not in outname): ax.margins(x=0)
    hep.cms.label(loc=0, ax=ax, label=extraText, rlabel='', data=True if 'preselection' in outname else False)
    hep.cms.lumitext(lumiText,ax=ax)

    if plot_ratio:
        yerr = np.nan_to_num(
            np.abs(
                poisson_conf_interval(data)
                - data
            )
            / (totalBkg + 1e-5)
        )
        rax.errorbar(x=bin_centers, y=data/(totalBkg+1e-5), yerr=yerr, xerr=None, **errorbar_style)
        '''
        hep.histplot(
            data / (totalBkg + 1e-5),
            yerr=yerr,
            ax=rax,
            histtype="errorbar",
            color="black",
            capsize=4,
        )
        '''
        rax.set_ylabel("Data/MC")
        rax.set_ylim([0,2])
        rax.grid()

    plt.savefig(outname)


def rebin(inHist, newBins):
    '''
    inHist  : TH1
    newBins : array with new bins (must be a subset of old bins)

    returns : new rebinned histogram
    '''
    print(f'\tRebinning {inHist.GetName()} to {len(newBins)-1} bins')
    nbins = len(newBins)
    hOut = inHist.Rebin(nbins-1, inHist.GetName(), newBins)
    hOut.SetDirectory(0)
    return hOut


redir = 'root://cmsxrootd.fnal.gov/'
fname = '{redir}/store/user/ammitra/XHYbbWW/studies/CR_SR_studies_{proc}_{year}.root'
fname = 'rootfiles/CR_SR_studies_{proc}_{year}.root'
fTest = ROOT.TFile.Open(fname.format(redir=redir,proc='ttbar-allhad',year='18'),'READ')
histNames = [i.GetName() for i in fTest.GetListOfKeys()]
histTitles = [i.GetTitle() for i in fTest.GetListOfKeys()]

def fileExists(proc,year):
    try:
        f = subprocess.check_output(f'ls rootfiles/ | grep CR | grep _{proc}_{year}.root',shell=True,text=True)
        return 1
    except:
        return 0


# Loop over years
for year in ['16','16APV','17','18']:
    for Rebin in [False,True]:
        for i,histName in enumerate(histNames):
            # plot results after kinematic preselection and after WW identification
            #if ('preselection' not in histName): continue# and ('stage1' not in histName): continue
            #if ('particleNet_mass' not in histName) and ('softdrop' not in histName) and ('vsQCD' not in histName): continue

            # plot results after H,W,W selection 
            if ('stage2' not in histName): continue
            if ('vsQCD' not in histName) and ('softdrop' not in histName) and ('particleNet_mass' not in histName): continue

            print(f'Plotting {histName}')

            if 'preselection' in histName:
                jetID = 'Jet ' + histName.split('_')[-1]
            else:
                if '_H_' in histName:
                    jetID = r'H'
                elif '_W1_' in histName:
                    jetID = r'$W_{1}$'
                elif '_W2_' in histName:
                    jetID = r'$W_{2}$'

            # Get binnings
            if ('particleNet_mass' in histName) or ('softdrop' in histName):
                edges = np.linspace(0,300,61)
                new_edges = array.array('d',np.linspace(0,300,31))
                new_edges_np = np.linspace(0,300,31)
                if 'particleNet_mass' in histName:
                    xtitle = r'%s $m_{reg}$ [GeV]'%(jetID)
                else: 
                    xtitle = r'%s $m_{SD}$ [GeV]'%(jetID)

            elif 'pt' in histName:
                edges = np.linspace(200,1200,101)
                new_edges = array.array('d',np.linspace(200,1200,51))
                new_edges_np = np.linspace(200,1200,51)
                xtitle = r'%s $p_T$ [GeV]'%(jetID)

            elif 'vsQCD' in histName:
                edges = np.linspace(0,1,51)
                new_edges = np.linspace(0,1,26)
                new_edges_np = np.linspace(0,1,26)
                if 'HbbvsQCD' in histName:
                    xtitle = r'%s $T_{Hbb}^{MD}$'%(jetID)
                elif 'WvsQCD' in histName:
                    xtitle = r'%s $T_{Wqq}^{MD}$'%(jetID)

            elif ('mhww' in histName) or ('mww' in histName):
                edges = np.linspace(0,3000,101)
                new_edges = array.array('d',np.linspace(0,3000,31))
                new_edges_np = np.linspace(0,3000,31)
                if 'mhww' in histName:
                    xtitle = r'$m_X$ [GeV]'
                else:
                    xtitle = r'$m_Y$ [GeV]'

            # get test histogram for zeros
            testHist = fTest.Get(histName)
            if Rebin: testHist = rebin(testHist,new_edges)
            testHist = hist2array(testHist)

            tt = [np.zeros_like(testHist),'red']
            wj = [np.zeros_like(testHist),'green']
            zj = [np.zeros_like(testHist),'blue']
            xy = [np.zeros_like(testHist),'black']
            st = [np.zeros_like(testHist),'purple']
            qcd = [np.zeros_like(testHist),'yellow']
            data = [np.zeros_like(testHist),'black']
            dib = [np.zeros_like(testHist),'lime']
            hbb  = [np.zeros_like(testHist),'teal']
            hww = [np.zeros_like(testHist),'grey']

            # diboson
            for proc in ['WW','ZZ','WZ']:
                if not fileExists(proc,year):
                    print(f'\t\t{proc} {year} does not exist')
                    continue

                print(f'	Adding histogram for {proc}_{year}')
                f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year=year),'READ')
                h = f.Get(histName)
                if Rebin: h = rebin(h,new_edges)
                a = hist2array(h)
                dib[0] += a
                f.Close()
            # hbb inclusive
            for proc in ['GluGluHToBB','VBFHToBB','ttHToBB','WplusH-HToBB-WToQQ','WminusH-HToBB-WToQQ','ZH-HToBB-ZToQQ','ggZH-HToBB-ZToQQ']:
                if not fileExists(proc,year):
                    print(f'\t\t{proc} {year} does not exist')
                    continue

                print(f'	Adding histogram for {proc}_{year}')
                f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year=year),'READ')
                h = f.Get(histName)
                if Rebin: h = rebin(h,new_edges)
                a = hist2array(h)
                hbb[0] += a
                f.Close()

            # hww inclusive
            for proc in ['GluGluHToWW-Pt-200ToInf-M-125','HWminusJ-HToWW-M-125','HWplusJ-HToWW-M-125','HZJ-HToWW-M-125','ttHToNonbb-M125']:
                if not fileExists(proc,year):
                    print(f'\t\t{proc} {year} does not exist')
                    continue

                print(f'	Adding histogram for {proc}_{year}')
                f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year=year),'READ')
                h = f.Get(histName)
                if Rebin: h = rebin(h,new_edges)
                a = hist2array(h)
                hww[0] += a
                f.Close()

            for proc in ['ttbar-allhad','ttbar-semilep']:
                if not fileExists(proc,year):
                    print(f'\t\t{proc} {year} does not exist')
                    continue

                print(f'	Adding histogram for {proc}_{year}')
                f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year=year),'READ')
                h = f.Get(histName)
                if Rebin: h = rebin(h,new_edges)
                a = hist2array(h)
                tt[0] += a
                f.Close()

            for proc in ['WJetsHT400','WJetsHT600','WJetsHT800']:
                if not fileExists(proc,year):
                    print(f'\t\t{proc} {year} does not exist')
                    continue

                print(f'	Adding histogram for {proc}_{year}')
                f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year=year),'READ')
                h = f.Get(histName)
                if Rebin: h = rebin(h,new_edges)
                a = hist2array(h)
                wj[0] += a
                f.Close()

            for proc in ['ZJetsHT400','ZJetsHT600','ZJetsHT800']:
                if not fileExists(proc,year):
                    print(f'\t\t{proc} {year} does not exist')
                    continue

                print(f'	Adding histogram for {proc}_{year}')
                f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year=year),'READ')
                h = f.Get(histName)
                if Rebin: h = rebin(h,new_edges)
                a = hist2array(h)
                zj[0] += a
                f.Close()

            for proc in ['NMSSM-XHY-1800-1200']:
                if not fileExists(proc,year):
                    print(f'\t\t{proc} {year} does not exist')
                    continue

                print(f'	Adding histogram for {proc}_{year}')
                f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year=year),'READ')
                h = f.Get(histName)
                if Rebin: h = rebin(h,new_edges)
                a = hist2array(h)
                xy[0] += a
                f.Close()

            for proc in ['QCDHT700','QCDHT1000','QCDHT1500','QCDHT2000']: # HT1000 didn't generate
                if not fileExists(proc,year):
                    print(f'\t\t{proc} {year} does not exist')
                    continue

                print(f'	Adding histogram for {proc}_{year}')
                f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year=year),'READ')
                h = f.Get(histName)
                if Rebin: h = rebin(h,new_edges)
                a = hist2array(h)
                qcd[0] += a
                f.Close()

            for proc in ['ST-antitop4f','ST-tW-antitop5f','ST-tW-top5f','ST-top4f']:
                if not fileExists(proc,year):
                    print(f'\t\t{proc} {year} does not exist')
                    continue

                print(f'	Adding histogram for {proc}_{year}')
                f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year=year),'READ')
                h = f.Get(histName)
                if Rebin: h = rebin(h,new_edges)
                a = hist2array(h)
                st[0] += a
                f.Close()

            datasets = {
                '16': ['DataF','DataG','DataH'],
                '16APV': ['DataB','DataC','DataD','DataE','DataF'],
                '17': ['DataB','DataC','DataD','DataE','DataF'],
                '18': ['DataA','DataB','DataC','DataD']
            }

            for proc in datasets[year]:
                if not fileExists(proc,year):
                    print(f'\t\t{proc} {year} does not exist')
                    continue

                print(f'	Adding histogram for {proc}_{year}')
                f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year=year),'READ')
                h = f.Get(histName)
                if Rebin: h = rebin(h,new_edges)
                a = hist2array(h)
                data[0] += a
                f.Close()

            total_withQCD = np.zeros_like(testHist)
            total_noQCD = np.zeros_like(testHist)
            for bkg in [tt,wj,zj,st,dib,hww,hbb]:
                total_noQCD += bkg[0]
            for bkg in [tt,wj,zj,st,dib,hww,hbb,qcd]:
                total_withQCD += bkg[0]


            lumis = {
                '16APV': r'$20 fb^{-1}$, 2016APV (13 TeV)',
                '16': r'$17 fb^{-1}$, 2016 (13 TeV)',
                '17': r'$41 fb^{-1}$, 2017 (13 TeV)',
                '18': r'$60 fb^{-1}$, 2018 (13 TeV)'
            }


            bkgHists = OrderedDict(
                [
                    (r'QCD',qcd),
                    (r'$t\bar{t}$',tt),
                    (r'W+Jets',wj),
                    (r'Z+Jets',zj),
                    (r'Single-top',st),
                    (r'Diboson',dib),
                    (r'HWW',hww),
                    (r'Hbb',hbb)
                ]
            )
            bkgHistsNoQCD = OrderedDict(
                [
                    (r'$t\bar{t}$',tt),
                    (r'W+Jets',wj),
                    (r'Z+Jets',zj),
                    (r'Single-top',st),
                    (r'Diboson',dib),
                    (r'HWW',hww),
                    (r'Hbb',hbb)
                ]
            )
            sigHists = OrderedDict([(r'$X_{1800}, Y_{1200}$',xy)])

            # First do with linear scale and no ratio plot
            plot_stack(
                outname=f'plots/{histName}_{year}{"_rebin" if Rebin else ""}.png',
                data=data[0],
                bkgs=bkgHists,
                sigs=sigHists,
                totalBkg=total_withQCD,
                edges=new_edges_np if Rebin else edges,
                title=histName,
                xtitle=xtitle,
                plot_ratio=False,
                lumiText=lumis[year],
                extraText='',
                logyFlag=False
            )
            # Now do it without QCD MC
            plot_stack(
                outname=f'plots/{histName}_{year}{"_rebin" if Rebin else ""}_noQCD.png',
                data=data[0],
                bkgs=bkgHistsNoQCD,
                sigs=sigHists,
                totalBkg=total_noQCD,
                edges=new_edges_np if Rebin else edges,
                title=histName,
                xtitle=xtitle,
                plot_ratio=False,
                lumiText=lumis[year],
                extraText='',
                logyFlag=False
            )


            '''
            # now do it with log scale and ratio plot
            bkgHists = OrderedDict(
                [
                    (r'Hbb',hbb),
                    (r'HWW',hww),
                    (r'Diboson',dib),
                    (r'ST',st),
                    (r'Z+Jets',zj),
                    (r'W+Jets',wj),
                    (r'$t\bar{t}$',tt),
                    ('QCD',qcd)
                ]
            )
            plot_stack(
                outname=f'plots/{histName}_{year}{"_rebin" if Rebin else ""}_logy.png',
                data=data[0],
                bkgs=bkgHists,
                sigs=sigHists,
                totalBkg=total_withQCD,
                edges=new_edges_np if Rebin else edges,
                title=histName,
                xtitle=xtitle,
                plot_ratio=True,
                lumiText=lumis[year],
                extraText='Work in progress',
                logyFlag=True
            )
            '''
