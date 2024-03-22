'''
Script to study the JMR/JMS-corrected pT of H/W/W candidates for regressed and softdrop mass cases
'''
import ROOT, time
from TIMBER.Analyzer import HistGroup, CutGroup, VarGroup
from TIMBER.Tools.Common import CompileCpp
ROOT.gROOT.SetBatch(True)
from XHYbbWW_class import XHYbbWW
import os
from collections import OrderedDict
from TIMBER.Tools.Plot import CompareShapes, EasyPlots

def Study(setname, era, massWindow=[60.,110.]):
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

    hists = []
    for particle in ['H','W1','W2']:
	for mass in ['msoftdrop','mregressed']:
	    print('plotting %s vs pT for %s'%(mass,particle))
	    hist_name = '%s_vs_pT_%s'%(mass,particle)
	    hist_title = '%s vs p_{T};m^{%s}_{%s} (GeV);p_{T} (GeV)'%(mass,'SD' if 'softdrop' in mass else 'reg', particle)
	    xvar = '%s_%s_corr'%(particle,mass)
	    yvar = '%s_pt_corr'%(particle)
	    hist = selection.a.DataFrame.Histo2D((hist_name,hist_title,50,0,200,50,350,2350),xvar,yvar,'norm')
	    hists.append(hist)

    f = ROOT.TFile.Open('rootfiles/RegressedMassStudies_{}_{}.root'.format(setname,era),'RECREATE')
    f.cd()
    c = ROOT.TCanvas('c','c')
    c.cd()
    c.Print('plots/RegressedMassStudies_{}_{}.pdf['.format(setname,era))
    c.Clear()
    for h in hists:
	c.Clear()
	h.Draw('COLZ')
	h.Write()
	c.Print('plots/RegressedMassStudies_{}_{}.pdf'.format(setname,era))
    c.Print('plots/RegressedMassStudies_{}_{}.pdf]'.format(setname,era))
    f.Close()

if __name__ == "__main__":
    CompileCpp('HWWmodules.cc')

    era = 18

    massWindow = []#[60.,110.]

    setname = 'NMSSM-XHY-1800-800'
    Study(setname,era,massWindow)
