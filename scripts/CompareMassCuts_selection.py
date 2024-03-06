import ROOT, time
from TIMBER.Analyzer import HistGroup, CutGroup, VarGroup
from TIMBER.Tools.Common import CompileCpp
ROOT.gROOT.SetBatch(True)
from XHYbbWW_class import XHYbbWW
import os
from collections import OrderedDict
from TIMBER.Tools.Plot import CompareShapes, EasyPlots

case1 = 'SR_pass'
case2 = 'SR_pass_mHreg_cut'
case3 = 'mWreg_cut_SR_pass'
case4 = 'mWreg_cut_SR_pass_mHreg_cut'

base_name = 'MXvMY_regressed_particleNet_{}__nominal'
fname = 'rootfiles/XHYbbWWselection_HT0_NMSSM-XHY-1800-800_17.root'

f = ROOT.TFile.Open(fname,'READ')

for mass in ['regressed','softdrop']:
    for proj in ['X','Y']:
	plot_filename = 'plots/selection_massCut_comparisons_{}_proj{}.png'.format(mass,proj)
	signal_hists, names, colors = OrderedDict(),OrderedDict(),OrderedDict()
	signames = ['NMSSM-XHY-1800-800']
	for sig in signames:
	    for case in [case1,case2,case3,case4]:
		hist = f.Get(base_name.format(case))
		hist_proj = getattr(hist, 'Projection%s'%proj)()
		signal_hists[sig+'_'+case] = hist_proj
		if case == case1:
		    colors[sig+'_'+case] = ROOT.kRed
		    names[sig+'_'+case]  = 'no mass cuts'
		elif case == case2:
		    colors[sig+'_'+case] = ROOT.kBlue
		    names[sig+'_'+case]  = 'm_{H} cut'
		elif case == case3:
		    colors[sig+'_'+case] = ROOT.kGreen
		    names[sig+'_'+case]  = 'm_{W} cut'
		else:
		    colors[sig+'_'+case] = ROOT.kBlack
		    names[sig+'_'+case]  = 'm_{H} and m_{W} cut'
	latex_varname = 'm_{%s}'%proj
	print('Plotting %s mass - projection %s'%(mass, proj))
	CompareShapes(
	    plot_filename,
	    year = 17,
	    prettyvarname=latex_varname,
	    bkgs={},
	    signals=signal_hists,
	    names=names,
	    colors=colors,
	    scale=False,
	    stackBkg=False
	)
		
