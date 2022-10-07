import ROOT, time
from TIMBER.Analyzer import HistGroup, Correction
from TIMBER.Tools.Common import CompileCpp
from collections import OrderedDict

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
    selection.a.ObjectFromCollection('Higgs','Trijet',0)
    selection.a.ObjectFromCollection('W1','Trijet',1)
    selection.a.ObjectFromCollection('W2','Trijet',2)
    kinOnly = selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXsecScale())
    # final cut on jet masses before moving on to 
    #kinOnly = selection.ApplyMassCuts()

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

    cutflowInfo = OrderedDict([
	('nHiggsMassCut',selection.nHiggsMassCut),
	('nW1MassCut',selection.nW1MassCut),
	('nW2MassCut',selection.nW2MassCut),
	('nWTag_CR',selection.nWTag_CR),
        ('higgsF_CR',selection.higgsF_CR),
        ('higgsL_CR',selection.higgsL_CR),
        ('higgsP_CR',selection.higgsP_CR),
        ('nWTag_SR',selection.nWTag_SR),
        ('higgsF_SR',selection.higgsF_SR),
        ('higgsL_SR',selection.higgsL_SR),
        ('higgsP_SR',selection.higgsP_SR)
    ])

    nLabels = len(cutflowInfo)
    hCutflow = ROOT.TH1F('cutflow', 'Number of events after each cut', nLabels, 0.5, nLabels+0.5)
    nBin = 1
    for label, value in cutflowInfo.items():
	hCutflow.GetXaxis().SetBinLabel(nBin, label)
	hCutflow.AddBinContent(nBin, value)
	nBin += 1
    hCutflow.Write()

    if not selection.a.isData:
        scale = ROOT.TH1F('scale','xsec*lumi/genEventSumw',1,0,1)
        scale.SetBinContent(1,selection.GetXsecScale())
        scale.Write()
        selection.a.PrintNodeTree('NodeTree_selection.pdf',verbose=True)

    print('%s sec'%(time.time()-start))

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
    args.trigEff = Correction("TriggerEff"+args.era,'TIMBER/Framework/include/EffLoader.h',['HWWtrigger2D_{}.root'.format(args.era if 'APV' not in args.era else 16),'Pretag'], corrtype='weight')
    XHYbbWW_selection(args)

