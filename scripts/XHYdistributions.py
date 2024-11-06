'''
   provide control distributions of jet quantities (pt, eta, phi) for each year for data and   bkg
   plotting in ROOT is a nightmare with python, so just use plotKinDist.py to plot them (python3)
'''
import ROOT, collections,sys,os
sys.path.append('./')
from optparse import OptionParser
from collections import OrderedDict

from TIMBER.Analyzer import HistGroup, Correction
from TIMBER.Tools.Common import CompileCpp, ExecuteCmd
from TIMBER.Tools.Plot import *

ROOT.gROOT.SetBatch(True)
from XHYbbWW_class import XHYbbWW


# variables to plot (keys = columns in DF, vals = latex names)
varnames = {
    'PNetW0': 'Leading AK8 jet ParticleNet W score',
    'PNetW1': 'Sublead AK8 jet 1 ParticleNet W score',
    'PNetW2': 'Sublead AK8 jet 2 ParticleNet W score',
    'PNetH0': 'Leading AK8 jet ParticleNet H score',
    'PNetH1': 'Sublead AK8 jet 1 ParticleNet H score',
    'PNetH2': 'Sublead AK8 jet 2 ParticleNet H score',
    'pt0': 'Leading AK8 jet p_{T}',
    'pt1': 'Sublead AK8 jet 1 p_{T}',
    'pt2': 'Sublead AK8 jet 2 p_{T}',
    'HT': "Sum of three jets' p_{T}",
    'mjjj': "Trijet invariant mass [GeV]",
    'eta0': 'Leading AK8 jet #eta',
    'eta1': 'Sublead AK8 jet 1 #eta',
    'eta2': 'Sublead AK8 jet 2 #eta',
    'phi0': 'Leading AK8 jet #varphi',
    'phi1': 'Sublead AK8 jet 1 #varphi',
    'phi2': 'Sublead AK8 jet 2 #varphi'
}


# main function to be called for processing
def select(setname, args):
    '''
	setname (str) = as appearing in dijet_nano/
	year    (str) = 16, 16APV, 17, 18
    '''
    year = args.era
    ROOT.ROOT.EnableImplicitMT(args.threads)
    selection = XHYbbWW('trijet_nano/%s_%s_snapshot.txt'%(setname,year),year,1,1)
    selection.OpenForSelection('None')	# apply corrections, define a few columns, etc (does NOT make cuts)
    selection.ApplyTrigs(args.trigEff)

    # kinematic definitions
    selection.a.Define('eta0','Trijet_eta[0]')
    selection.a.Define('eta1','Trijet_eta[1]')
    selection.a.Define('eta2','Trijet_eta[2]')
    selection.a.Define('phi0','Trijet_phi[0]')
    selection.a.Define('phi1','Trijet_phi[1]')
    selection.a.Define('phi2','Trijet_phi[2]')
    selection.a.Define('PNetW0','Trijet_particleNetMD_WvsQCD[0]')
    selection.a.Define('PNetW1','Trijet_particleNetMD_WvsQCD[1]')
    selection.a.Define('PNetW2','Trijet_particleNetMD_WvsQCD[2]')
    selection.a.Define('PNetH0','Trijet_particleNetMD_HbbvsQCD[0]')
    selection.a.Define('PNetH1','Trijet_particleNetMD_HbbvsQCD[1]')
    selection.a.Define('PNetH2','Trijet_particleNetMD_HbbvsQCD[2]')
    for jet in [0,1,2]:
	selection.a.Define('JetVector_{}'.format(jet),'hardware::TLvector(Trijet_pt[{0}], Trijet_eta[{0}], Trijet_phi[{0}], Trijet_msoftdrop[{0}])'.format(jet))
    selection.a.Define('mjjj','hardware::InvariantMass({JetVector_0,JetVector_1,JetVector_2})')

    selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXsecScale())

    # book a group to save histos
    out = HistGroup('{}_{}'.format(setname,year))
    for varname in varnames.keys():
	histname = '{}_{}_{}'.format(setname, year, varname)
 	if ('pt' in varname):
	    hist_tuple = (varname,varname,100,350,2350)
	elif (varname == 'HT'):
	    hist_tuple = (varname,varname,200,350,4350)
	elif 'mj' in varname:
	    hist_tuple = (varname,varname,36,400,4000) # 36 bins, 100 GeV wide
	elif 'eta' in varname:
	    hist_tuple = (varname,varname,48,-2.4,2.4)
	elif 'phi' in varname:
	    hist_tuple = (varname,varname,64,-3.14,3.14)
	elif 'PNet' in varname:
	    hist_tuple = (varname,varname,100,0.0,1.0)
	# Project dataframe into a histogram (hist name/binning tuple, variable to plot from dataframe, weight)
	print('Plotting: {}'.format(hist_tuple))
	hist = selection.a.GetActiveNode().DataFrame.Histo1D(hist_tuple,varname,'weight__nominal')
	#hist = selection.a.GetActiveNode().DataFrame.Histo1D(hist_tuple,varname)
	hist.GetValue()	# This gets the actual TH1 instead of a pointer to the TH1
	out.Add(varname,hist)

    return out

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-y', type=str, dest='era',
			action='store', required=True,
			help='Year to process')
    parser.add_argument('-t', type=int, dest='threads',
			action='store', required=False,
			default=2, help='Number of threads to use. On LPC, keep default at 2')
    parser.add_argument('--HT', type=str, dest='HT',
                        action='store', default='0',
                        help='Value of HT to cut on')

    args = parser.parse_args()
    
    args.trigEff = Correction("TriggerEff"+args.era,'TIMBER/Framework/include/EffLoader.h',['triggers/HWWtrigger2D_HT{}_{}.root'.format(args.HT,args.era if 'APV' not in args.era else 16),'Pretag'], corrtype='weight')

    histgroups = {}
    for setname in ['Data', 'ttbar-allhad', 'ttbar-semilep', 'QCDHT700','QCDHT1000','QCDHT1500','QCDHT2000','MX1800-MY125','MX1800-MY1000','MX3000-MY2000']:
	# TEMPORARYi UNTIL OFFICIAL SAMPLES
	# for now, only have 2017 signal MC
	if 'MX' in setname and args.era != '17':
	    continue
	histgroup = select(setname, args)
	outfile = ROOT.TFile.Open('rootfiles/kinDist_{}_{}.root'.format(setname,args.era),'RECREATE')
	outfile.cd()
	histgroup.Do('Write')
	outfile.Close()
	del histgroup

    # now hadd all the relevant ones
    ExecuteCmd('hadd -f rootfiles/kinDist_QCD_{0}.root rootfiles/kinDist_QCDHT*_{0}.root'.format(args.era))
    ExecuteCmd('hadd -f rootfiles/kinDist_ttbar_{0}.root rootfiles/kinDist_ttbar-*_{0}.root'.format(args.era))


