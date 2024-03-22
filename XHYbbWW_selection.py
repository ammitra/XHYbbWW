import ROOT, time
from TIMBER.Analyzer import HistGroup, Correction
from TIMBER.Tools.Common import CompileCpp
from collections import OrderedDict
import TIMBER.Tools.AutoJME as AutoJME

#ROOT.gROOT.SetBatch(True)

from XHYbbWW_class import XHYbbWW

def getHbbEfficiencies(analyzer, tagger, SRorCR, wp_loose, wp_tight):
    ''' call this function after calling ApplyWTag() '''
    print('Obtaining efficiencies in {}'.format(SRorCR))
    tagger = 'H_' + tagger
    print('checkpoint 1')
    start = analyzer.GetActiveNode()
    print('checkpoint 2')
    nTot = analyzer.DataFrame.Sum("genWeight").GetValue()
    print('checkpoint 3')
    print("nTot = {}".format(nTot))
    analyzer.Cut("Eff_L_{}_cut".format(SRorCR),"{0} > {1} && {0} < {2}".format(tagger, wp_loose, wp_tight))
    nL = analyzer.DataFrame.Sum("genWeight").GetValue()
    print("nL = {}".format(nL))
    analyzer.SetActiveNode(start)
    analyzer.Cut("Eff_T_{}_cut".format(SRorCR),"{0} > {1}".format(tagger, wp_tight))
    nT = analyzer.DataFrame.Sum("genWeight").GetValue()
    print("nT = {}".format(nT))
    effL = nL/nTot
    effT = nT/nTot
    analyzer.SetActiveNode(start)
    print('{}: effL = {}%'.format(SRorCR, effL*100.))
    print('{}: effT = {}%'.format(SRorCR, effT*100.))
    return effL, effT

def getWTagEfficiencies(analyzer, tagger, wp, idx, tag):
    print('Obtaining efficiencies for jet at idx {}'.format(idx))
    start = analyzer.GetActiveNode()
    nTot = analyzer.DataFrame.Sum("genWeight").GetValue()
    print("nTot = {}".format(nTot))
    analyzer.Cut("Eff_jet{}_{}_cut".format(idx, tag),"{} > {}".format(tagger, wp))
    nT = analyzer.DataFrame.Sum("genWeight").GetValue()
    print('nT = {}'.format(nT))
    eff = nT/nTot
    print('SR: eff = {}'.format(eff*100.))
    analyzer.SetActiveNode(start)
    return eff

def applyHbbScaleFactors(analyzer, tagger, variation, SRorCR, eff_loose, eff_tight, wp_loose, wp_tight, WMassCut):
    '''
	creates PNetHbbSFHandler object and creates the original and updated tagger categories
	must be called ONLY once, after calling ApplyWPick_Signal() so proper Higgs vect is created
	Therefore, we have to prepend the tagger with 'Higgs_'
    '''
    print('Applying SFs in {}'.format(SRorCR))
    # instantiate Scale Factor class: {WPs}, {effs}, "year", variation
    CompileCpp('PNetHbbSFHandler p_%s%s = PNetHbbSFHandler({0.8,0.98}, {%f,%f}, "20%s", %i);'%(SRorCR, WMassCut, eff_loose, eff_tight, args.era, variation))
    # now create the column with original tagger category values (0: fail, 1: loose, 2: tight)
    analyzer.Define("OriginalTagCats","p_{}.createTag({})".format(SRorCR+WMassCut, tagger))
    # now create the column with *new* tagger categories, after applying logic. MUST feed in the original column (created in last step)
    analyzer.Define("NewTagCats","p_{}.updateTag(OriginalTagCats, H_pt_corr, {})".format(SRorCR+WMassCut, tagger))


def XHYbbWW_selection(args):
    print('PROCESSING {} {}'.format(args.setname,args.era))
    start = time.time()
    signal = False

    # gather all snapshots
    selection = XHYbbWW('trijet_nano/{}_{}_snapshot.txt'.format(args.setname,args.era),args.era,1,1)
    selection.OpenForSelection(args.variation)

    # apply HT cut due to improved trigger effs
    before = selection.a.DataFrame.Count()
    selection.a.Cut('HT_cut','HT > {}'.format(args.HT))
    after = selection.a.DataFrame.Count()

    # Apply regressed mass cut
    selection.nBeforeMregCut = selection.getNweighted()
    selection.AddCutflowColumn(selection.nBeforeMregCut, 'nBeforeMregCut')
    selection.a.Cut('regressedmass_cut','Trijet_mregressed_corr[0] > 50 && Trijet_mregressed_corr[1] > 50 && Trijet_mregressed_corr[2] > 50')
    selection.nAfterMregCut = selection.getNweighted()
    selection.AddCutflowColumn(selection.nAfterMregCut, 'nAfterMregCut')

    selection.ApplyTrigs(args.trigEff)

    # scale factor application
    if ('NMSSM' in args.setname):
	signal = True
	# determine which scale factors we're varying (nom:0, up:1, down:2)
	if (args.variation == 'PNetHbb_up'):
	    HVar = 1
	    WVar = 0
	elif (args.variation == 'PNetHbb_down'):
	    HVar = 2
	    WVar = 0
        elif (args.variation == 'PNetWqq_up'):
	    HVar = 0
	    WVar = 1
        elif (args.variation == 'PNetWqq_down'):
            HVar = 0
            WVar = 2
	else:	# if doing any other variation, keep SFs nominal
            HVar = 0
            WVar = 0

    kinOnly = selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXsecScale())

    out = ROOT.TFile.Open('rootfiles/XHYbbWWselection_HT{}_{}_{}{}.root'.format(args.HT, args.setname, args.era, '_'+args.variation if args.variation != 'None' else ''), 'RECREATE')
    out.cd()

    for t in ['particleNet']:
	w_tagger = '{}MD_WvsQCD'.format(t)
	h_tagger = '{}MD_HbbvsQCD'.format(t)

	# SIGNAL
	if signal:
	    # CONTROL REGION - INVERT W CUT 
	    print("CONTROL REGION --------------------------------------------------------------------------------------------------------")
	    selection.a.SetActiveNode(kinOnly)
	    e0CR = getWTagEfficiencies(analyzer=selection.a, tagger='Trijet_'+w_tagger+'[0]', wp=0.8, idx=0, tag='cr0')
	    e1CR = getWTagEfficiencies(analyzer=selection.a, tagger='Trijet_'+w_tagger+'[1]', wp=0.8, idx=1, tag='cr1')
	    e2CR = getWTagEfficiencies(analyzer=selection.a, tagger='Trijet_'+w_tagger+'[2]', wp=0.8, idx=2, tag='cr2')
	    selection.ApplyWPick_Signal(WTagger='Trijet_'+w_tagger, HTagger='Trijet_'+h_tagger, pt='Trijet_pt_corr', WScoreCut=0.8, 
					eff0=e0CR, eff1=e1CR, eff2=e2CR, year=args.era, WVariation=WVar, invert=True, 
					WMass='Trijet_mregressed_corr', massWindow=[])
	    eff_L_CR, eff_T_CR = getHbbEfficiencies(analyzer=selection.a, tagger=h_tagger, SRorCR='CR', wp_loose=0.8, wp_tight=0.98)
	    applyHbbScaleFactors(analyzer=selection.a, tagger='H_'+h_tagger, variation=HVar, SRorCR='CR', eff_loose=eff_L_CR, 
				 eff_tight=eff_T_CR, wp_loose=0.8, wp_tight=0.98, WMassCut='')
	    passfailCR = selection.ApplyHiggsTag('CR', tagger='H_'+h_tagger, signal=signal)
	    # SIGNAL REGION 
            print("SIGNAL REGION --------------------------------------------------------------------------------------------------------")
	    '''
            selection.a.SetActiveNode(kinOnly)
            e0SR = getWTagEfficiencies(analyzer=selection.a, tagger='Trijet_'+w_tagger+'[0]', wp=0.8, idx=0, tag='sr0')
            e1SR = getWTagEfficiencies(analyzer=selection.a, tagger='Trijet_'+w_tagger+'[1]', wp=0.8, idx=1, tag='sr1')
            e2SR = getWTagEfficiencies(analyzer=selection.a, tagger='Trijet_'+w_tagger+'[2]', wp=0.8, idx=2, tag='sr2')
            selection.ApplyWPick_Signal(WTagger='Trijet_'+w_tagger, HTagger='Trijet_'+h_tagger, pt='Trijet_pt_corr', WScoreCut=0.8,
                                        eff0=e0SR, eff1=e1SR, eff2=e2SR, year=args.era, WVariation=WVar, invert=False, 
					WMass='Trijet_mregressed_corr', massWindow=[])
	    eff_L_SR, eff_T_SR = getHbbEfficiencies(analyzer=selection.a, tagger=h_tagger, SRorCR='SR', wp_loose=0.8, wp_tight=0.98)
            applyHbbScaleFactors(analyzer=selection.a, tagger='H_'+h_tagger, variation=HVar, SRorCR='SR', eff_loose=eff_L_SR,
                                 eff_tight=eff_T_SR, wp_loose=0.8, wp_tight=0.98, WMassCut='_noWMassCut')
            passfailSR = selection.ApplyHiggsTag('SR', tagger='H_'+h_tagger, signal=signal, WMassCut=False)
	    '''
	    
	    # Now do the SR with the W mass requirements applied 
	    selection.a.SetActiveNode(kinOnly)
            e0SR = getWTagEfficiencies(analyzer=selection.a, tagger='Trijet_'+w_tagger+'[0]', wp=0.8, idx=0, tag='sr0')
            e1SR = getWTagEfficiencies(analyzer=selection.a, tagger='Trijet_'+w_tagger+'[1]', wp=0.8, idx=1, tag='sr1')
            e2SR = getWTagEfficiencies(analyzer=selection.a, tagger='Trijet_'+w_tagger+'[2]', wp=0.8, idx=2, tag='sr2')
	    massWindow = [60., 110.]
	    selection.ApplyWPick_Signal(WTagger='Trijet_'+w_tagger, HTagger='Trijet_'+h_tagger, pt='Trijet_pt_corr', WScoreCut=0.8,
                                        eff0=e0SR, eff1=e1SR, eff2=e2SR, year=args.era, WVariation=WVar, invert=False,
					WMass='Trijet_mregressed_corr', massWindow=massWindow)
            eff_L_SR, eff_T_SR = getHbbEfficiencies(analyzer=selection.a, tagger=h_tagger, SRorCR='SR', wp_loose=0.8, wp_tight=0.98)
            applyHbbScaleFactors(analyzer=selection.a, tagger='H_'+h_tagger, variation=HVar, SRorCR='SR', eff_loose=eff_L_SR,
                                 eff_tight=eff_T_SR, wp_loose=0.8, wp_tight=0.98, WMassCut='_WMassCut')
	    passfailSR_WMassCut = selection.ApplyHiggsTag('SR', tagger='H_'+h_tagger, signal=signal, WMassCut=True)


	# Everything else
	else:
	    # CONTROL REGION 
	    selection.a.SetActiveNode(kinOnly)
	    selection.ApplyWPick(tagger='Trijet_'+w_tagger, invert=True, WMass='', massWindow=[])
	    passfailCR = selection.ApplyHiggsTag('CR', tagger='H_'+h_tagger, signal=signal)
	    # SIGNAL REGION
	    '''
	    selection.a.SetActiveNode(kinOnly)
	    selection.ApplyWPick(tagger='Trijet_'+w_tagger, invert=False, WMass='', massWindow=[])
	    passfailSR = selection.ApplyHiggsTag('SR', tagger='H_'+h_tagger, signal=signal, WMassCut=False)
	    '''
	    # Now do the SR with W mass requirement applied 
	    selection.a.SetActiveNode(kinOnly)
	    massWindow = [60., 110.]
	    selection.ApplyWPick(tagger='Trijet_'+w_tagger, invert=False, WMass='Trijet_mregressed_corr', massWindow=massWindow)
            passfailSR_WMassCut = selection.ApplyHiggsTag('SR', tagger='H_'+h_tagger, signal=signal, WMassCut=True)


    	binsX = [45,0,4500]	# nbins, low, high
    	binsY = [35,0,3500]
	region_rdict = {
	    "SR": passfailSR_WMassCut,
	    "CR": passfailCR
	}
    	for region, rdict in region_rdict.items():
	    for flp, node in rdict.items():
		# The node will have columns for mX and mY calculated with both softdrop and regressed masses (both corrected).
		# We want to make templates for both to see how they vary
		# UPDATE Mar 14 2024 - only use the softdrop for 4-vectors and regressed for cuts (as per JME)
		for mass in ['softdrop']:#,'regressed']:
		    mod_name = "{}_{}_{}_{}".format(mass,t,region,flp)
		    mod_title = "{} {} {}".format(region,flp,mass)
		    selection.a.SetActiveNode(node)
		    print('Evaluating {}'.format(mod_title))
		    mX = 'mhww_%s'%(mass)
		    mY = 'mww_%s'%(mass)
		    templates = selection.a.MakeTemplateHistos(ROOT.TH2F('MXvMY_%s'%mod_name, 'MXvMY %s with %s'%(mod_title,t),binsX[0],binsX[1],binsX[2],binsY[0],binsY[1],binsY[2]),[mX,mY])
		    templates.Do('Write')

    cutflowInfo = OrderedDict([
	('nBeforeMregCut',selection.nBeforeMregCut),    # before cut on regressed mass > 50
	('nAfterMregCut',selection.nAfterMregCut),	# after cut on regressed mass > 50
	('nWTag_CR',selection.nWTag_CR),		# control region
        ('higgsF_CR',selection.nHF_CR),			# no mH_reg or mW_reg cut
        ('higgsL_CR',selection.nHL_CR),			# no mH_reg or mW_reg cut 
        ('higgsP_CR',selection.nHP_CR),			# no mH_reg or mW_reg cut 
	('higgsL_CR_mHreg',selection.nHL_CR_mreg),	# after mH_reg anti-cut in CR Loose
	('higgsP_CR_mHreg',selection.nHP_CR_mreg),	# after mH_reg anti-cut in CR Pass
        #('nWTag_SR',selection.nWTag_SR),		# signal region, no mass cuts
        #('higgsF_SR',selection.nHF_SR),			# same
        #('higgsL_SR',selection.nHL_SR),			# same
        #('higgsP_SR',selection.nHP_SR),			# same
	('nWTag_SR_massCut',selection.nWTag_SR_massWindow), # mW_reg cut
	('higgsL_SR_mHreg_mWreg',selection.nHL_SR_mreg_WMass), # mH_reg & mW_reg cut
	('higgsP_SR_mHreg_mWreg',selection.nHP_SR_mreg_WMass), # mH_reg & mW_reg cut
        #('higgsL_SR_mHreg',selection.nHL_SR_mreg),      # SR_loose, mH_reg cut, no mW_reg
        #('higgsP_SR_mHreg',selection.nHP_SR_mreg)	# SR_loose, mH_reg cut, no mW_reg
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
        #selection.a.PrintNodeTree('NodeTree_selection.pdf',verbose=True)

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
    parser.add_argument('--HT', type=str, dest='HT',
                        action='store', default='0',
                         help='Value of HT to cut on')

    args = parser.parse_args()
    #args.threads = 4

    # We must apply the 2017B triffer efficiency to ~12% of the 2017 MC
    # This trigEff correction is passed to ApplyTrigs() in the XHYbbWW_selection() function
    if ('Data' not in args.setname) and (args.era == '17'): # we are dealing with MC from 2017
	cutoff = 0.11283 # fraction of total JetHT data belonging to 2017B (11.283323383%)
	TRand = ROOT.TRandom3()
	rand = TRand.Uniform(0.0, 1.0)
	if rand < cutoff:
	    print('Applying 2017B trigger efficiency')
	    args.trigEff = Correction("TriggerEff17",'TIMBER/Framework/include/EffLoader.h',['triggers/HWWtrigger2D_HT{}_17B.root'.format(args.HT),'Pretag'],corrtype='weight')
	else:
	    args.trigEff = Correction("TriggerEff17",'TIMBER/Framework/include/EffLoader.h',['triggers/HWWtrigger2D_HT{}_17.root'.format(args.HT),'Pretag'],corrtype='weight')
    else:
	args.trigEff = Correction("TriggerEff"+args.era,'TIMBER/Framework/include/EffLoader.h',['triggers/HWWtrigger2D_HT{}_{}.root'.format(args.HT,args.era if 'APV' not in args.era else 16),'Pretag'], corrtype='weight')

    CompileCpp('HWWmodules.cc')
    if ('NMSSM' in args.setname):
	CompileCpp('ParticleNet_HbbSF.cc')
    XHYbbWW_selection(args)

