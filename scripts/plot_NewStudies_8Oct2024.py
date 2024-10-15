import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplhep as hep
from collections import OrderedDict

# Options for plotting
stack_style = {
    'edgecolor': (0, 0, 0, 0.5),
}
errorbar_style = {
    'linestyle': 'none',
    'marker': '.',      # display a dot for the datapoint
    'elinewidth': 2,    # width of the errorbar line
    'markersize': 20,   # size of the error marker
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
    lumiText = r'$138 fb^{-1} (13 TeV)$',
    extraText = 'Preliminary',
    units='GeV'):

    plt.style.use([hep.style.CMS])
    fig, ax = plt.subplots()

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
    ax.set_ylabel(f'Events / {width} {units}')
    ax.set_xlabel(xtitle)

    '''
    # plot data (blind it)
    if ('pass' in outname) and ('NO_QCD' in outname):
        if ('H_SR0_mregressed' not in outname):
            print(f'\tnot plotting data in {outname}')
        else:
            print(f'\tBlinding Higgs mass window [100,150] GeV for {outname}')
            mask = np.where(np.logical_and(edges >= 100, edges <= 150))
            blinded_data = np.copy(data)
            lower_errors, upper_errors = poisson_conf_interval(blinded_data)
            yerr = [blinded_data - lower_errors, upper_errors - blinded_data]
            blinded_data[mask] = np.nan
            #yerr[mask] = np.nan
            bin_centers = (edges[:-1] + edges[1:])/2
            ax.errorbar(x=bin_centers, y=blinded_data, yerr=yerr, xerr=None, label='Data', **errorbar_style)

    elif ('fail' in outname) and ('NO_QCD' in outname):
        if ('H_SR0_mregressed' not in outname):
            print(f'\tPlotting data in {outname} (FAIL)')
            lower_errors, upper_errors = poisson_conf_interval(data)
            yerr = [data - lower_errors, upper_errors - data]
            bin_centers = (edges[:-1] + edges[1:])/2
            ax.errorbar(x=bin_centers, y=data, yerr=yerr, xerr=None, label='Data', **errorbar_style)
        else:
            print(f'\tBlinding Higgs mass window [100,150] GeV for {outname}')
            mask = np.where(np.logical_and(edges >= 100, edges <= 150))
            blinded_data = np.copy(data)
            lower_errors, upper_errors = poisson_conf_interval(blinded_data)
            yerr = [blinded_data - lower_errors, upper_errors - blinded_data]
            blinded_data[mask] = np.nan
            #yerr[mask] = np.nan
            bin_centers = (edges[:-1] + edges[1:])/2
            ax.errorbar(x=bin_centers, y=blinded_data, yerr=yerr, xerr=None, label='Data', **errorbar_style)
    '''


    # plot signals
    for key,val in sigs.items():
        sigarr = val[0]
        # Determine a reasonable scaling to keep the maximum on the order of the data maximum 
        bkg_max = totalBkg.max()   # get bkg max
        sig_max = sigarr.max()     # get signal max
        scaling = bkg_max/sig_max
        ax.step(x=edges, y=np.hstack([sigarr,sigarr[-1]])*scaling, where='post', color=val[1], label=r'%s $\times$ %s'%(key,round(scaling,1)))
    
    if logyFlag:
        ax.set_ylim(0.001, totalBkg.max()*1e5)
        ax.set_yscale('log')
    else:
        ax.set_ylim(0, totalBkg.max()*1.5)

    ax.legend()
    ax.margins(x=0)
    hep.cms.label(loc=0, ax=ax, label=extraText, rlabel='')
    hep.cms.lumitext(lumiText,ax=ax)

    plt.savefig(outname)


redir = 'root://cmsxrootd.fnal.gov/'
fname = '{redir}/store/user/ammitra/XHYbbWW/studies/NewSelectionStudies_{proc}_{year}.root'
fTest = ROOT.TFile.Open(fname.format(redir=redir,proc='ttbar-allhad',year='18'),'READ')
histNames = [i.GetName() for i in fTest.GetListOfKeys()]
histTitles = [i.GetTitle() for i in fTest.GetListOfKeys()]

for i,histName in enumerate(histNames):

    # at this point, we're sticking with 2.5% mistag rate on W candidates
    if ('STAGE1' not in histName) and ('SR0' not in histName): continue

    if histName == 'cutflow':
        testEff = fTest.Get('cutflow')
        testEff.Reset()

        tt_eff = testEff.Clone()
        wj_eff = testEff.Clone()
        zj_eff = testEff.Clone()
        xy_eff = testEff.Clone()
        st_eff = testEff.Clone()
        qcd_eff = testEff.Clone()

        for proc in ['ttbar-allhad','ttbar-semilep']:
            f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year='18'),'READ')
            eff = f.Get('cutflow')
            tt_eff.Add(eff)

        for proc in ['WJetsHT400','WJetsHT600','WJetsHT800']:
            f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year='18'),'READ')
            eff = f.Get('cutflow')
            wj_eff.Add(eff)

        for proc in ['ZJetsHT400','ZJetsHT600','ZJetsHT800']:
            f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year='18'),'READ')
            eff = f.Get('cutflow')
            zj_eff.Add(eff)

        for proc in ['NMSSM-XHY-1800-1200']:
            f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year='18'),'READ')
            eff = f.Get('cutflow')
            xy_eff.Add(eff)

        for proc in ['QCDHT700','QCDHT1500','QCDHT2000']: # HT1000 didn't generate
            f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year='18'),'READ')
            eff = f.Get('cutflow')
            qcd_eff.Add(eff)

        for proc in ['ST-antitop4f','ST-tW-antitop5f','ST-tW-top5f','ST-top4f']:
            f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year='18'),'READ')
            eff = f.Get('cutflow')
            st_eff.Add(eff)

        effs = {'ttbar':tt_eff,'WJets':wj_eff,'ZJets':zj_eff,'QCD':qcd_eff,'XHY-1800-1200':xy_eff,'ST':st_eff}
        for proc, eff in effs.items():
            fOut=ROOT.TFile.Open(f'rootfiles/NewSelectionStudies_{proc}_cutflow_18.root','RECREATE')
            fOut.cd()
            eff.Write()
            fOut.Close()

    print(histName)
    # Get binnings
    if ('mregressed' in histName):
        edges = np.linspace(0,300,61)
        xtitle = r'$m_{reg}$ [GeV]'
    elif 'pt' in histName:
        edges = np.linspace(200,1200,101)
        xtitle = r'$p_T$ [GeV]'
    elif 'particleNet' in histName:
        edges = np.linspace(0,1,51)
        if 'HbbvsQCD' in histName:
            xtitle = r'$T_{Hbb}^{MD}$'
        elif 'WvsQCD' in histName:
            xtitle = r'T_{Wqq}^{MD}'
    elif ('mhww' in histName) or ('mww' in histName):
        edges = np.linspace(0,3000,101)
        if 'mhww' in histName:
            xtitle = r'$m_X$ [GeV]'
        else:
            xtitle = r'$m_Y$ [GeV]'

    # get test histogram for zeros
    testHist = fTest.Get(histName)
    testHist = hist2array(testHist)


    tt = [np.zeros_like(testHist),'red']
    wj = [np.zeros_like(testHist),'green']
    zj = [np.zeros_like(testHist),'blue']
    xy = [np.zeros_like(testHist),'black']
    st = [np.zeros_like(testHist),'purple']
    qcd = [np.zeros_like(testHist),'yellow']
    data = [np.zeros_like(testHist),'black']



    for proc in ['ttbar-allhad','ttbar-semilep']:
        f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year='18'),'READ')
        h = f.Get(histName)
        a = hist2array(h)
        tt[0] += a

    for proc in ['WJetsHT400','WJetsHT600','WJetsHT800']:
        f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year='18'),'READ')
        h = f.Get(histName)
        a = hist2array(h)
        wj[0] += a

    for proc in ['ZJetsHT400','ZJetsHT600','ZJetsHT800']:
        f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year='18'),'READ')
        h = f.Get(histName)
        a = hist2array(h)
        zj[0] += a

    for proc in ['NMSSM-XHY-1800-1200']:
        f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year='18'),'READ')
        h = f.Get(histName)
        a = hist2array(h)
        xy[0] += a

    for proc in ['QCDHT700','QCDHT1500','QCDHT2000']: # HT1000 didn't generate
        f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year='18'),'READ')
        h = f.Get(histName)
        a = hist2array(h)
        qcd[0] += a

    for proc in ['ST-antitop4f','ST-tW-antitop5f','ST-tW-top5f','ST-top4f']:
        f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year='18'),'READ')
        h = f.Get(histName)
        a = hist2array(h)
        st[0] += a

    for proc in ['DataA','DataB','DataC','DataD']:
        f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year='18'),'READ')
        h = f.Get(histName)
        a = hist2array(h)
        data[0] += a


    total = np.zeros_like(testHist)
    for bkg in tt,wj,zj,qcd,st:
        total += bkg[0]


    bkgHists = OrderedDict(
        [
            (r'QCD',qcd),
            (r'$t\bar{t}$',tt),
            (r'W+Jets',wj),
            (r'Z+Jets',zj),
            (r'single-top',st)
        ]
    )
    sigHists = OrderedDict([(r'$X_{1800}, Y_{1200}$',xy)])

    # First do with QCD MC 
    plot_stack(
        outname=f'plots/{histName}.png',
        data=data[0],
        bkgs=bkgHists,
        sigs=sigHists,
        totalBkg=total,
        edges=edges,
        title=histName,
        xtitle=xtitle,
        lumiText='2018',
        extraText=''
    )

    # then do without QCD MC 
    bkgHists = OrderedDict(
        [
            (r'$t\bar{t}$',tt),
            (r'W+Jets',wj),
            (r'Z+Jets',zj),
            (r'single-top',st)
        ]
    )
    plot_stack(
        outname=f'plots/{histName}_NO_QCD.png',
        data=data[0],
        bkgs=bkgHists,
        sigs=sigHists,
        totalBkg=total,
        edges=edges,
        title=histName,
        xtitle=xtitle,
        lumiText='2018',
        extraText=''
    )

