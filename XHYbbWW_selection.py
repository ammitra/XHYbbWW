import ROOT, time
from TIMBER.Analyzer import HistGroup, Correction
from TIMBER.Tools.Common import CompileCpp

ROOT.gROOT.SetBatch(True)

from XHYbbWW_class import XHYbbWW

# not for use with data
def XHYbbWW_selection(args):
    print('PROCESSING {} {}'.format(args.setname,args.era))
    start = time.time()

    # gather all snapshots
    selection = XHYbbWW('trijet_nano/{}_{}_snapshot.txt'.format(args.setname,args.era),int(args.era),1,1)
    #selection.OpenForSelection(args.variation)
    kinOnly = selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXSecScale())

    # write the SR, CR hists to file
    out = ROOT.Tfile.Open('rootfiles/XHYbbWWselection_{}_{}{}.root'.format(args.setname,args.era,'_'+args.variation if args.variation != 'None' else ''), 'RECREATE')
    out.cd()

    for t in ['particleNet']:
	w_tagger = '{}_WvsQCD'.format(t)
	higgs_tagger = '{}_HbbvsQCD'.format(t)
	
	# signal region
	
