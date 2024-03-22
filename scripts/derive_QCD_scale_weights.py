'''
Script that performs selection of H/W/W candidates subject to all systematics
and saves out the H/W/W candidate jets' pT subject to all 8 QCD scale uncertainties.

Then, plots them using MPLHEP to derive the uncertainties that have the greatest effect.

plotting requires python 3, so just skip this if running on LPC (py2 environment)
'''

import os
import ROOT
from argparse import ArgumentParser

if 'CMSSW_BASE' not in os.environ:
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    import mplhep as hep
    from root_numpy import hist2array
    import ctypes
    from mpl_toolkits.mplot3d import Axes3D
    from matplotlib import cm

def derive_qcd_scale_weights(args):
    # Even if running on signal, ignore this since we are just going to be using the nominal versions of all corrections
    signal = False
    # Open the snapshot file(s), do corrections and obtain nominal
    selection = XHYbbWW(args.infile, args.era, 1, 1)
    selection.setname = args.setname
    selection.OpenForSelection('None') # nominal only
    selection.ApplyTrigs(args.trigEff)
    # Define weights for the 8 LHE QCD scale weights
    for i in range(8):
	selection.a.Define('LHEweight%s'%i,"LHEScaleWeight[%s]"%i)
    # Normalize to xsec and lumi
    selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXsecScale())

    # Select the H/W/W candidates
    massWindow = [60., 110.]
    w_tagger = 'particleNetMD_WvsQCD'
    h_tagger = 'particleNetMD_HbbvsQCD'
    selection.ApplyWPick(tagger='Trijet_'+w_tagger, invert=False, WMass='Trijet_mregressed_corr', massWindow=massWindow)
    #passfailSR = selection.ApplyHiggsTag('SR', tagger='H_'+h_tagger, signal=signal, WMassCut=True)

    # Make histos of the H/W/W candidate pT under each variation
    histos = []
    for cand in ['H','W1','W2']:
	# first do nominal
	print('Generating histos of %s-candidate pT'%cand)
	print('\tnominal')
	nom = selection.a.DataFrame.Histo1D(('%s_pt__nominal'%cand,';%s candidate p_T;Events / 50 GeV'%cand,16,200,1000),'%s_pt_corr'%cand)
	histos.append(nom)
	# now do the 8 variations
	for i in range(8):
	    print('\tQCD scale %s'%i)
	    hpt = selection.a.DataFrame.Histo1D(('%s_pt__%s'%(cand,i),';%s candidate p_T;Events / 50 GeV'%cand,16,200,1000),'%s_pt_corr'%cand,'LHEweight%s'%i)
	    histos.append(hpt)

    # save the histos to an output file 
    plot_filename = 'pt_%s_%s.root'%(args.setname,args.era)
    out_f = ROOT.TFile.Open(plot_filename, 'RECREATE')
    out_f.cd()
    for h in histos:
	h.Write()
    out_f.Close()

def plot(args):
    # Get the root file containing the histos
    plot_filename = 'pt_%s_%s.root'%(args.setname,args.era)
    f = ROOT.TFile.Open(plot_filename)
    
    labels = ["(1.0,1.0)","(0.5,0.5)","(1.0,0.5)","(2.0,0.5)","(0.5,1.0)","(2.0,1.0)","(0.5,2.0)","(1.0,2.0)","(2.0,2.0)"]

    # Loop over the H/W/W candidates
    for cand in ['H','W1','W2']:
	histos = []
	print('Plotting pT of %s candidate'%cand)
	# Nominal first
	print('\tnominal')
	hNom 		= f.Get('%s_pt__nominal'%cand)
	nomYield 	= hNom.Integral()
	hNom, edges     = hist2array(hNom,return_edges=True)
	histos.append(hNom)
	# Now QCD scale variations
	for i in range(8):
	    hTemp	= f.Get('%s_pt__%s'%(cand,i))
	    if (i==0 or i==7): print("QCD scale {}/nominal = {0:.2f}".format(i,hTemp.Integral()/nomYield))
	    hTemp	= hist2array(hTemp,return_edges=False)
	    histos.append(hTemp)
	# Now plot
	plt.style.use([hep.style.CMS])
	f, ax = plt.subplots()
	hep.histplot(histos, bins=edges[0],label=labels)
	plt.legend(title="$(\mu_{F},\mu_{R})$ factors")
	hep.cms.text("Work in progress",loc=0)
	hep.cms.lumitext(text="2018 (13 TeV)", ax=ax, fontname=None, fontsize=None)
	ax.set_xlim([300.,1000.])
	plt.xlabel("%s candidate $p_{T}$ [GeV]"%cand,horizontalalignment='right', x=1.0)
	plt.ylabel("Events / 50 GeV",horizontalalignment='right', y=1.0)
	foutName = "%s_%s_%s_pT_scaleVariations"%(args.setname,args.era,cand)
	print("Saving {0}.pdf".format(foutName))
	plt.savefig("{0}.pdf".format(foutName), bbox_inches='tight')
	plt.savefig("{0}.png".format(foutName), bbox_inches='tight')

	ax.set_yscale("log")
	plt.savefig("{0}_log.pdf".format(foutName), bbox_inches='tight')
	plt.savefig("{0}_log.png".format(foutName), bbox_inches='tight')

	plt.cla()
	plt.clf()

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
                        action='store', required=False,
                        help='Setname to process.')
    parser.add_argument('-i', type=str, dest='infile',
                        action='store', required=False,
                        help='Input snapshot file')
    parser.add_argument('-y', type=str, dest='era',
                        action='store', required=False,
                        help='Year of set (16, 17, 18).')
    parser.add_argument('--plotfilename', type=str, dest='plotfilename',
                        action='store', default='None',
                        help='Name of the output file containing histograms')

    args = parser.parse_args()

    if 'CMSSW_BASE' in os.environ:
	from TIMBER.Analyzer import HistGroup, Correction
	from TIMBER.Tools.Common import CompileCpp
	from XHYbbWW_class import XHYbbWW
    	if ('Data' not in args.infile) and (args.era == '17'): # we are dealing with MC from 2017
            cutoff = 0.11283 # fraction of total JetHT data belonging to 2017B (11.283323383%)
            TRand = ROOT.TRandom3()
            rand = TRand.Uniform(0.0, 1.0)
            if rand < cutoff:
            	print('Applying 2017B trigger efficiency')
            	args.trigEff = Correction("TriggerEff17",'TIMBER/Framework/include/EffLoader.h',['triggers/HWWtrigger2D_HT{}_17B.root'.format(0),'Pretag'],corrtype='weight')
            else:
            	args.trigEff = Correction("TriggerEff17",'TIMBER/Framework/include/EffLoader.h',['triggers/HWWtrigger2D_HT{}_17.root'.format(0),'Pretag'],corrtype='weight')
    	else:
            args.trigEff = Correction("TriggerEff"+args.era,'TIMBER/Framework/include/EffLoader.h',['triggers/HWWtrigger2D_HT{}_{}.root'.format(0,args.era if 'APV' not in args.era else 16),'Pretag'], corrtype='weight')

    	CompileCpp('HWWmodules.cc')

    	derive_qcd_scale_weights(args)
    else:
	plot(args)
