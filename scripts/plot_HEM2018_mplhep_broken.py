'''
Script to plot the full 2018 dataset before and after applying the HEM correction
'''
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplhep as hep
from collections import OrderedDict
from XHYbbWW_class import XHYbbWW
from TIMBER.Analyzer import Correction, CutGroup, ModuleWorker, analyzer
import ROOT

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

eta_before = ROOT.TH1D('eta_before','eta_before',80,-3,3); eta_before.Reset()
eta_after  = ROOT.TH1D('eta_after','eta_after',80,-3,3); eta_after.Reset()
phi_before = ROOT.TH1D('phi_before','phi_before',80,-3.14,3.14); phi_before.Reset()
phi_after  = ROOT.TH1D('phi_after','phi_after',80,-3.14,3.14); phi_after.Reset()

etas_before = []
etas_after  = []
phis_before = []
phis_after  = []

for era in ['A']:#['A','B','C','D']:
    print(f'Running over JetHT dataset Data{era}.....')
    selection = XHYbbWW(f'trijet_nano/Data{era}_18_snapshot.txt','18',1,1)

    # Apply lumi filter to get clean data
    lumiFilter = ModuleWorker(f'LumiFilter_Data{era}','TIMBER/Framework/include/LumiFilter.h',[18])
    selection.a.Cut(f'lumiFilter_Data{era}',lumiFilter.GetCall(evalArgs={"lumi":"luminosityBlock"}))

    # Get the distribution before the HEM veto
    for var in ['eta','phi']:
        print(f'Obtaining distribution of {var} before HEM veto')
        if var == 'eta':
            model_before = (f'{var}before','{var}before',80,-3,3)
        else:
            model_before = (f'{var}before','{var}before',80,-3.14,3.14) 
        hBefore = selection.a.DataFrame.Histo1D(model_before,f'Trijet_{var}')
        hBefore.SetDirectory(0)
        if var == 'eta':
            etas_before.append(hBefore)
        else:
            phis_before.append(hBefore)

    # Perform the HEM veto
    HEM_worker = ModuleWorker(f'HEM_drop_Data{era}','TIMBER/Framework/include/HEM_drop.h',[f'Data{era}'])
    selection.a.Cut(f'HEM_Data{era}','%s[0] > 0'%(HEM_worker.GetCall(evalArgs={"FatJet_eta":"Trijet_eta","FatJet_phi":"Trijet_phi"})))

    # Get the distribution after the HEM veto 
    for var in ['eta','phi']:
        print(f'Obtaining distribution of {var} after HEM veto')
        if var == 'eta':
            model_after = (f'{var}after','{var}after',80,-3,3)
        else:
            model_after = (f'{var}after','{var}after',80,-3.14,3.14)
        hAfter = selection.a.DataFrame.Histo1D(model_after,f'Trijet_{var}')
        hAfter.SetDirectory(0)
        if var == 'eta':
            etas_after.append(hAfter)
        else:
            phis_after.append(hAfter)

# Sum all histograms before and after
for h in etas_before:
    print(f'\tAdding {h.GetName()}')
    eta_before.Add(h.GetPtr())
for h in etas_after:
    print(f'\tAdding {h.GetName()}')
    eta_after.Add(h.GetPtr())
for h in phis_before:
    print(f'\tAdding {h.GetName()}')
    phi_before.Add(h.GetPtr())
for h in phis_after:
    print(f'\tAdding {h.GetName()}')
    phi_after.Add(h.GetPtr())

# Plot with mplhep
eta_before = hist2array(eta_before)
eta_after  = hist2array(eta_after)
phi_before = hist2array(phi_before)
phi_after  = hist2array(phi_after)

xedges = np.linspace(-3, 3, 81)
yedges = np.linspace(-3.14, 3.14, 81)

print(eta_before,phi_before)
print(eta_after,phi_after)


for time in ['before','after']:
    print(f'Plotting 2D eta vs phi {time} HEM veto...')
    if time == 'before':
        x = eta_before; y = phi_before
    else:
        x = eta_after; y = phi_after
    H, xedges, yedges = np.histogram2d(x, y, bins=(xedges, yedges))
    plt.style.use([hep.style.CMS])
    fig, ax = plt.subplots()
    hep.hist2dplot(H, xedges, yedges, labels=False);
    ax.set_ylabel(r'$\phi$')
    ax.set_xlabel(r'$\eta$')
    hep.cms.label(loc=0, ax=ax, label='WiP', rlabel='')
    hep.cms.lumitext('2018 (13 TeV)',ax=ax)
    plt.savefig(f'plots/{time}_HEM_veto.pdf')
