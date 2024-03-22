import ROOT, time
from TIMBER.Analyzer import HistGroup, CutGroup, VarGroup
from TIMBER.Tools.Common import CompileCpp
ROOT.gROOT.SetBatch(True)
from XHYbbWW_class import XHYbbWW
import os
from collections import OrderedDict
from TIMBER.Tools.Plot import CompareShapes, EasyPlots

def NMinus1(setname, era, massWindow=False):
    # Open the snapshots
    selection = XHYbbWW('trijet_nano/{}_{}_snapshot.txt'.format(setname,era), era, 1, 1)
    # perform JECs, define Trijet vector
    selection.OpenForSelection('None')
    # identify W1, W2, and H from the three valid jet candidates
    if massWindow:
	selection.ApplyWPick('Trijet_particleNetMD_WvsQCD', invert=False, WMass='Trijet_mregressed_corr', massWindow=massWindow)
    else:
	selection.ApplyWPick('Trijet_particleNetMD_WvsQCD', invert=False)
    # Get the normalization
    norm = selection.GetXsecScale()
    selection.a.Define('norm','genWeight*%s'%norm)
    # Now perform mass window cut on the W1 and W1. Add some dummy cuts
    NCuts = CutGroup('NCuts')
    NCuts.Add('mww_dummy', 'mww_softdrop > 0')
    NCuts.Add('w_mass_cut', '(W1_msoftdrop_corr > 60 && W1_msoftdrop_corr < 110) && (W2_msoftdrop_corr > 60 && W2_msoftdrop_corr < 110)')
    # now see how this cut influences the W,H,X,Y candidate masses (for both softdrop and regressed masses)
    plotVars = VarGroup('plotVars')
    plotVars.Add('mW1_sd','W1_msoftdrop_corr')
    plotVars.Add('mW2_sd','W2_msoftdrop_corr')
    plotVars.Add('mH_sd','H_msoftdrop_corr')
    plotVars.Add('mY_sd','mww_softdrop')
    plotVars.Add('mX_sd','mhww_softdrop')
    plotVars.Add('mW1_reg','W1_mregressed_corr')
    plotVars.Add('mW2_reg','W2_mregressed_corr')
    plotVars.Add('mH_reg','H_mregressed_corr')
    plotVars.Add('mY_reg','mww_regressed')
    plotVars.Add('mX_reg','mhww_regressed')


    nodeToPlot = selection.a.Apply(plotVars)
    nMinus1Nodes = selection.a.Nminus1(NCuts,node=nodeToPlot)
    nMinus1Hists = HistGroup('nminus1Hists')

    binning = {
	'mW1': [24,40,160],
	'mW2': [24,40,160],
	'mH': [24,40,160],
	'mY': [45,0,4500],
	'mX': [35,0,3500]
    }

    # Loop over every N-1 node (there will be 3: mww_dummy, w_mass_cut, full) and plot for each
    for nkey in nMinus1Nodes.keys():
	if (nkey == 'full') or ('dummy' in nkey): continue # we want the w_mass_cut key, since *no* cuts have been applied to this node apart from the dummy cut
	for var, bins in binning.items():
	    for mass in ['sd','reg']:
		varname = var + '_%s'%mass
		print('Plotting variable %s...'%varname)
	    	hist_tuple = (varname,varname,bins[0],bins[1],bins[2])
		print('\tHisto1D((%s,%s,%s,%s,%s),%s,"norm")'%(varname,varname,bins[0],bins[1],bins[2],varname))
	    	hist = nMinus1Nodes[nkey].DataFrame.Histo1D(hist_tuple,varname,'norm')
	    	hist.GetValue()
	    	nMinus1Hists.Add(varname,hist)

    return nMinus1Hists

if __name__ == "__main__":
    CompileCpp('HWWmodules.cc')

    era = 18

    massWindow = [60.,110.]

    histgroups = {}
    varnames = []
    setnames = [
	'NMSSM-XHY-1800-800',
	'ttbar-allhad','ttbar-semilep',
	'WJetsHT400','WJetsHT600','WJetsHT600',
	'ZJetsHT400','ZJetsHT600','ZJetsHT800',
	'WW', 'WZ', 'ZZ', 
	'ggZH-HToBB-ZToQQ','GluGluHToBB','GluGluHToWW-Pt-200ToInf-M-125',
	'ST-antitop4f','ST-top4f','ST-tW-antitop5f','ST-tW-top5f',
	'ttHToBB','ttHToNonbb-M125',
	'WminusH-HToBB-WToQQ','WplusH-HToBB-WToQQ','ZH-HToBB-ZToQQ',
	'HWminusJ-HToWW-M-125','HWplusJ-HToWW-M-125','HZJ-HToWW-M-125'
    ]
    bkgnames = [i for i in setnames if 'NMSSM' not in i]
    signames = [i for i in setnames if 'NMSSM' in i]

    for setname in setnames:
	print('Analyzing {} for 20{}'.format(setname,era))
	rootfile_name = 'rootfiles/WMassCut_Nminus1{}_{}_{}.root'.format('_WMassSelection' if massWindow else '',setname,era)

	if not os.path.isfile(rootfile_name):
	    print('Must run analysis first...')
	    histgroup = NMinus1(setname, era)
	    f = ROOT.TFile.Open(rootfile_name,'RECREATE')
	    f.cd()
	    print('Writing histograms...')
	    histgroup.Do('Write')
	else:
	    print('Opening {}'.format(rootfile_name))
	    f = ROOT.TFile.Open(rootfile_name,'READ')

	histgroups[setname] = HistGroup(setname)

	for key in f.GetListOfKeys():
	    keyname = key.GetName()
	    inhist = f.Get(key.GetName())
	    inhist.SetDirectory(0)
	    histgroups[setname].Add(keyname,inhist)
	    if keyname not in varnames:
		varnames.append(keyname)
	f.Close()

    latex_varnames = {
        'mW1_sd': 'm_{W_{1}}^{SD}',
        'mW2_sd': 'm_{W_{2}}^{SD}',
        'mY_sd': 'm_{Y}^{SD}',
        'mX_sd': 'm_{X}^{SD}',
	'mH_sd': 'm_{H}^{SD}',
        'mW1_reg': 'm_{W_{1}}^{reg}',
        'mW2_reg': 'm_{W_{2}}^{reg}',
        'mY_reg': 'm_{Y}^{reg}',
        'mX_reg': 'm_{X}^{reg}',
        'mH_reg': 'm_{H}^{reg}'
    }
    colors = {
        'ttbar': ROOT.kRed,
        'WJets': ROOT.kBlue,
        'ZJets': ROOT.kGreen,
	'DIB': ROOT.kOrange,
	'ggf': ROOT.kPink,
	'ST': ROOT.kBlack,
	'ttH': ROOT.kTeal,
	'HV': ROOT.kAzure,
	'HVJ': ROOT.kCyan
    }
    names = {
	'ttbar': 't#bar{t}',
	'WJets': 'W+jets',
	'ZJets': 'Z+jets',
        'DIB': 'Diboson',
        'ggf': 'ggf',
        'ST': 'single top',
        'ttH': 'ttH',
        'HV': 'HV',
        'HVJ': 'HV+J'
    }

    for sig in signames:
	colors[sig] = ROOT.kCyan-int((int(sig[10:-4])-1200)/600)
	names[sig] = '({},{}) [GeV]'.format(sig.split('-')[2],sig.split('-')[3])
    for varname in varnames:
	plot_filename = 'plots/WMassCut_Nminus1{}_{}_{}.png'.format('_WMassSelection' if massWindow else '',varname,era)
	# ordered dicts to plot processes in the specified order
	bkg_hists, signal_hists = OrderedDict(),OrderedDict()
	for bkg in bkgnames:
	    histgroups[bkg][varname].SetTitle('%s N-1 20%s'%(setname,era))
	    if 'ttbar' in bkg:
		if 'ttbar' not in bkg_hists.keys():
		    bkg_hists['ttbar'] = histgroups[bkg][varname].Clone('ttbar_'+varname)
		else:
            	    bkg_hists['ttbar'].Add(histgroups[bkg][varname])
	    elif 'WJets' in bkg:
		if 'WJets' not in bkg_hists.keys():
		    bkg_hists['WJets'] = histgroups[bkg][varname].Clone('WJets_'+varname)
		else:
		    bkg_hists['WJets'].Add(histgroups[bkg][varname])
	    elif 'ZJets' in bkg:
		if 'ZJets' not in bkg_hists.keys():
		    bkg_hists['ZJets'] = histgroups[bkg][varname].Clone('ZJets_'+varname)
		else:
		    bkg_hists['ZJets'].Add(histgroups[bkg][varname])
	    elif (len(bkg)==2): # diboson
		if 'DIB' not in bkg_hists.keys():
		    bkg_hists['DIB'] = histgroups[bkg][varname].Clone('DIB_'+varname)
		else:
		    bkg_hists['DIB'].Add(histgroups[bkg][varname])
	    elif ('gg' in bkg) or ('GluGlu' in bkg):
                if 'ggF' not in bkg_hists.keys():
                    bkg_hists['ggF'] = histgroups[bkg][varname].Clone('ggF_'+varname)
                else:
                    bkg_hists['ggF'].Add(histgroups[bkg][varname])
	    elif 'ST-' in bkg:
                if 'ST' not in bkg_hists.keys():
                    bkg_hists['ST'] = histgroups[bkg][varname].Clone('ST_'+varname)
                else:
                    bkg_hists['ST'].Add(histgroups[bkg][varname])
	    elif 'ttH' in bkg:
                if 'ttH' not in bkg_hists.keys():
                    bkg_hists['ttH'] = histgroups[bkg][varname].Clone('ttH_'+varname)
                else:
                    bkg_hists['ttH'].Add(histgroups[bkg][varname])
	    elif ('WminusH' in bkg) or ('WplusH' in bkg) or (bkg == 'ZH-HToBB-ZToQQ'):
                if 'HV' not in bkg_hists.keys():
                    bkg_hists['HV'] = histgroups[bkg][varname].Clone('HV'+varname)
                else:
                    bkg_hists['HV'].Add(histgroups[bkg][varname])
	    elif ('HWminusJ' in bkg) or ('HWplusJ' in bkg) or ('HZJ' in bkg):
                if 'HVJ' not in bkg_hists.keys():
                    bkg_hists['HVJ'] = histgroups[bkg][varname].Clone('HVJ'+varname)
                else:
                    bkg_hists['HVJ'].Add(histgroups[bkg][varname])

	for sig in signames:
	    signal_hists[sig] = histgroups[sig][varname]

	print('Plotting %s'%plot_filename)
	CompareShapes(
	    plot_filename,
	    era,
	    latex_varnames[varname],
	    bkgs=bkg_hists,
	    signals=signal_hists,
	    names=names,
	    colors=colors,
	    scale=True,
	    stackBkg=True
	)

    # now just plot the signal only, under the influence of the softdrop vs regressed mass reconstrution 
    for var in ['mW1','mW2','mY','mX','mH']:
	plot_filename =  'plots/WMassCut_Nminus1_SigOnly_{}_{}.png'.format(var,era)
	signal_hists, names, colors = OrderedDict(), OrderedDict(), OrderedDict()
        for sig in signames:
	    for mass in ['sd','reg']:
		varname = '%s_%s'%(var,mass)
            	signal_hists[sig+'_'+mass] = histgroups[sig][varname]
		colors[sig+'_'+mass] = ROOT.kRed if mass=='sd' else ROOT.kBlue
		names[sig+'_'+mass] = '({},{}) [GeV] ({})'.format(sig.split('-')[2],sig.split('-')[3],mass)
	latex_varnames = {
	    'mW1': 'm_{W_{1}}',
	    'mW2': 'm_{W_{2}}',
	    'mY': 'm_{Y}',
	    'mX': 'm_{X}',
	    'mH': 'm_{H}'
	}
        print('Plotting %s'%plot_filename)
        CompareShapes(
            plot_filename,
            era,
            latex_varnames[var],
            bkgs={},
            signals=signal_hists,
            names=names,
            colors=colors,
            scale=True,
            stackBkg=False
        )
