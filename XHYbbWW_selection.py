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
    selection.OpenForSelection(args.variation)
    selection.ApplyTrigs(args.trigEff)
    selection.a.Define('Trijet_vect','hardware::TLvector(Trijet_pt, Trijet_eta, Trijet_phi, Trijet_msoftdrop)')
    selection.a.Define('H_vect','hardware::TLvector(Trijet_pt[0], Trijet_eta[0], Trijet_phi[0], Trijet_msoftdrop[0])')
    selection.a.Define('W1_vect','hardware::TLvector(Trijet_pt[1], Trijet_eta[1], Trijet_phi[1], Trijet_msoftdrop[1])')
    selection.a.Define('W2_vect','hardware::TLvector(Trijet_pt[2], Trijet_eta[2], Trijet_phi[2], Trijet_msoftdrop[2])')
    selection.a.Define('Y','hardware::InvariantMass({W1_vect + W2_vect})')
    selection.a.Define('X','hardware::InvariantMass({H_vect + W1_vect + W2_vect})')
    selection.a.ObjectFromCollection('LeadHiggs','Trijet',0)
    selection.a.ObjectFromCollection('LeadW','Trijet',1)
    selection.a.ObjectFromCollection('SubleadW','Trijet',2)
    selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXsecScale())
    # final cut on jet masses before moving on to 
    kinOnly = selection.ApplyMassCuts()

    out = ROOT.TFile.Open('rootfiles/XHYbbWWselection_{}_{}{}.root'.format(args.setname, args.era, '_'+args.variatoon if args.variation != 'None' else ''), 'RECREATE')
    out.cd()

    for t in ['particleNet']:
	w_tagger = '{}_WvsQCD'.format(t)
	h_tagger = '{}_HbbvsQCD'.format(t)

	# control region
	print('---------- CONTROL REGION ----------')
	selection.a.SetActiveNode(kinOnly)
	selection.ApplyWTag('CR', w_tagger)	
	FLP_CR = selection.ApplyHiggsTag('CR', h_tagger)

	# signal region
	print('---------- SIGNAL REGION ----------')
	selection.a.SetActiveNode(kinOnly)
	selection.ApplyWTag('SR', w_tagger)
	FLP_SR = selection.ApplyHiggstag('SR', h_tagger)

    binsX = [35,0,3500]	# nbins, low, high
    binsY = [35,0,3500]
    for region, rdict in {"SR":FLP_SR,"CR":FLP_CR}.items():
	for flp, node in rdict.items():
            mod_name = "{}_{}_{}".format(t,region,flp)
            mod_title = "{} {}".format(region,flp)
            selection.a.SetActiveNode(node)
	    print('Evaluating {}'.format(mod_title))
	    templates = selection.a.MakeTemplateHistos(ROOT.TH2F('MXvMY_%s'%mod_name, 'MXvMY %s with %s'%(mod_title,t),binsX[0],binsX[1],binsX[2],binsY[0],binsY[1],binsY[2]),['X','Y'])
	    templates.Do('Write')

    if not selection.a.isData:
        scale = ROOT.TH1F('scale','xsec*lumi/genEventSumw',1,0,1)
        scale.SetBinContent(1,selection.GetXsecScale())
        scale.Write()
        selection.a.PrintNodeTree('NodeTree_selection.pdf',verbose=True)

    print('%s sec'%(time.time()-start))

# Deprecated
'''
    # write the SR, CR hists to file
    out = ROOT.TFile.Open('rootfiles/XHYbbWWselection_{}_{}{}.root'.format(args.setname,args.era,'_'+args.variation if args.variation != 'None' else ''), 'RECREATE')
    out.cd()

    for t in ['particleNet']:
	w_tagger = '{}_WvsQCD'.format(t)
	higgs_tagger = '{}_HbbvsQCD'.format(t)
	# gather our nodes in dicts for later use
	SR = {}
	CR = {}

	# signal region - vary Hbb, keep W>0.8
	Hbb = [0.8, 0.98]
	W_SR = [0.8]
	#W_CR = [0.3, 0.8]	# old CR
	W_CR = [0.05, 0.8]      # new CR for more statistics

	for region in ['SR', 'CR']:
	    if (region == 'SR'):
                regions = selection.MXvsMY(t, Hbb, W_SR)
	    else:
		regions = selection.MXvsMY(t, Hbb, W_CR)
	    selection.a.SetActiveNode(kinOnly)
	    # the X, Y invariant masses are already defined above, just use them. 
	    for r in range(3):
	        selection.a.SetActiveNode(kinOnly)
	        flp = selection.a.Apply(regions[r])	# fail, loose, pass
	        # store the nodes in their respective dict key
	        if (r == 0):
		    if (region == 'SR'):
		        SR['fail'] = flp
		    else:
			CR['fail'] = flp
	        elif (r == 1):
		    if (region == 'SR'):
		        SR['loose'] = flp
		    else:
			CR['loose'] = flp
	        else:
		    if (region == 'SR'):
	                SR['pass'] = flp
		    else:
			CR['pass'] = flp

	# now we have two dicts containing the Fail, Loose, Pass nodes for both SR and CR
	binsX = [35,0,3500]	# nbins, low, high
	binsY = [35,0,3500]
	for region, rdict in {"SR":SR, "CR":CR}.items():     # region, dict of region's f/l/p
	    for flp, node in rdict.items():		     # f/l/p, corresponding node
		mod_name = "{}_{}_{}".format(t, region, flp) # tagger_region_f/l/p
		mod_title = "{} {}".format(region, flp)	     # region f/l/p
		selection.a.SetActiveNode(node)		     # use X,Y as found in this node
		print('Evaluating {}'.format(mod_title))
		templates = selection.a.MakeTemplateHistos(ROOT.TH2F('MXvMY_%s'%mod_name, 'MXvMY %s with %s'%(mod_title,t),binsX[0],binsX[1],binsX[2],binsY[0],binsY[1],binsY[2]),['X','Y'])	# ROOT TH2F, then variables to be plotted ([x,y'])
		templates.Do('Write')

    if not selection.a.isData:
        scale = ROOT.TH1F('scale','xsec*lumi/genEventSumw',1,0,1)
        scale.SetBinContent(1,selection.GetXsecScale())
        scale.Write()
        selection.a.PrintNodeTree('NodeTree_selection.pdf',verbose=True)

    print('%s sec'%(time.time()-start))
'''


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
                        action='store', required=True,
                        help='Setname to process.')
    parser.add_argument('-y', type=str, dest='era',
                        action='store', required=True,
                        help='Year of set (16, 17, 18).')
    parser.add_argument('-v', type=str, dest='variation',
                        action='store', default='None',
                        help='JES_up, JES_down, JMR_up,...')

    args = parser.parse_args()
    args.trigEff = Correction("TriggerEff"+args.era,'TIMBER/Framework/include/EffLoader.h',['HWWtrigger2D_%s.root'%args.era,'Pretag'], corrtype='weight')
    XHYbbWW_selection(args)

