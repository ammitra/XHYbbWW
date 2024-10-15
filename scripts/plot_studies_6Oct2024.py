import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplhep as hep
from collections import OrderedDict

fig_style = {
    'figsize': (10, 10),
    'dpi': 100
}
ratio_fig_style = {
    'figsize': (10, 10),
    'gridspec_kw': {'height_ratios': (3, 1)},
    'dpi': 100
}

# Options for plotting
stack_style = {
    'edgecolor': (0, 0, 0, 0.5),
}
hatch_style = {
    'facecolor': 'none',
    'edgecolor': (0, 0, 0, 0.5),
    'linewidth': 0,
    'hatch': '///',
}
errorbar_style = {
    'linestyle': 'none',
    'marker': '.',      # display a dot for the datapoint
    'elinewidth': 2,    # width of the errorbar line
    'markersize': 20,   # size of the error marker
    'capsize': 0,       # size of the caps on the errorbar (0: no cap fr)
    'color': 'k',       # black 
}
shaded_style = {
    'facecolor': (0,0,0,0.3),
    'linewidth': 0
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
    

def plot_stack(
    outname,
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

    # plot signals
    for key,val in sigs.items():
        sigarr = val[0]
        scaling = 150.0
        ax.step(x=edges, y=np.hstack([sigarr,sigarr[-1]])*scaling, where='post', color=val[1], label=r'%s $\times$ %s'%(key,scaling))
    
    if logyFlag:
        ax.set_ylim(0.001, totalBkg.max()*1e5)
        ax.set_yscale('log')
    else:
        ax.set_ylim(0, totalBkg.max()*1.38)

    ax.legend()
    ax.margins(x=0)
    hep.cms.label(loc=0, ax=ax, label=extraText, rlabel='')
    hep.cms.lumitext(lumiText,ax=ax)

    plt.savefig(outname)


redir = 'root://cmsxrootd.fnal.gov/'
fname = '{redir}/store/user/ammitra/XHYbbWW/studies/Studies_{proc}_{year}_varNone.root'
fTest = ROOT.TFile.Open(fname.format(redir=redir,proc='ttbar-allhad',year='18'),'READ')
histNames = [i.GetName() for i in fTest.GetListOfKeys()]
histTitles = [i.GetTitle() for i in fTest.GetListOfKeys()]

for i,histName in enumerate(histNames):

    print(histName)
    # Get binnings
    if ('mregressed' in histName):
        edges = np.linspace(0,300,61)
        xtitle = r'$m_{reg}$ [GeV]'
    elif 'pt' in histName:
        edges = np.linspace(200,2200,101)
        xtitle = r'$p_T$ [GeV]'
    elif 'particleNet' in histName:
        edges = np.linspace(0,1,51)
        tagger = histTitles[i].split(' ')[0].split('_')[-1]
        xtitle = r'$T_{%s}^{MD}$'%(tagger)
    elif ('mx' in histName) or ('my' in histName):
        edges = np.linspace(0,3000,101)
        if 'mx' in histName:
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

    for proc in ['QCDHT700','QCDHT1000','QCDHT1500','QCDHT2000']:
        f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year='18'),'READ')
        h = f.Get(histName)
        a = hist2array(h)
        qcd[0] += a

    for proc in ['ST-antitop4f','ST-tW-antitop5f','ST-tW-top5f','ST-top4f']:
        f = ROOT.TFile.Open(fname.format(redir=redir,proc=proc,year='18'),'READ')
        h = f.Get(histName)
        a = hist2array(h)
        st[0] += a

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

    plot_stack(
        outname=f'plots/{histName}.png',
        bkgs=bkgHists,
        sigs=sigHists,
        totalBkg=total,
        edges=edges,
        title=histName,
        xtitle=xtitle,
        lumiText='2018',
        extraText='Simulation'
    )