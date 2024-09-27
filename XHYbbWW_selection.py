import ROOT, time
from TIMBER.Analyzer import HistGroup, Correction, Node
from TIMBER.Tools.Common import CompileCpp
from collections import OrderedDict
import TIMBER.Tools.AutoJME as AutoJME
from XHYbbWW_class import XHYbbWW
#from memory_profiler import profile

#@profile
def selection(args):
    print(f'Processing {args.setname} {args.year} for selection and 2D histogram creation.....')
    start = time.time()
    selection = XHYbbWW(f'trijet_nano/{args.setname}_{args.year}_snapshot.txt',args.year,int(args.ijob),int(args.njobs))
    selection.OpenForSelection(args.variation)
    selection.ApplyTrigs(args.trigEff)

    # Apply tagging (signal) or mistagging (ttbar) scale factors
    #eosdir  = 'root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/TaggerEfficiencies'
    #effpath = f'{eosdir}/{args.setname}_{args.year}_Efficiencies.root'
    effpath = f'ParticleNetSFs/EfficiencyMaps/{args.setname}_{args.year}_Efficiencies.root'
    w_tagger = 'particleNetMD_WvsQCD'
    h_tagger = 'particleNetMD_HbbvsQCD'
    w_wp = 0.8
    h_wp = 0.98
    if ('ttbar' in args.setname) or ('NMSSM' in args.setname):
        CompileCpp('ParticleNetSFs/TopMergingFunctions.cc')
        selection.a.Define('Trijet_GenMatchCats','classifyProbeJets({0,1,2}, Trijet_phi, Trijet_eta, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother)')
        # Pass the category to the constructor so the class can use tagging or mistagging systematics automatically
        category = 'ttbar' if 'ttbar' in args.setname else 'signal'

        PNet_HbbTagging_corr = Correction(
            name        = 'PNetMD_Hbb_%stag'%('mis' if category=='ttbar' else ''),
            #script      = 'ParticleNetSFs/PNetXbbSF_weight.cc',
            script      = 'ParticleNetSFs/PNetXbbSF_weight.cc',
            constructor = [args.year, category, effpath, h_wp],
            mainFunc    = 'eval',
            corrtype    = 'weight',
            columnList  = ['Trijet_pt_corr', 'Trijet_eta', 'Trijet_particleNetMD_HbbvsQCD', 'Trijet_GenMatchCats']
        )
        selection.a.AddCorrection(
            correction  = PNet_HbbTagging_corr,
            evalArgs    = {'pt':'Trijet_pt_corr', 'eta':'Trijet_eta', 'PNetXbb_score':'Trijet_particleNetMD_HbbvsQCD', 'jetCat':'Trijet_GenMatchCats'}
        )

        selection.a.DataFrame.Display(['PNetMD_Hbb_%stag__nom'%('mis' if category=='ttbar' else '')]).Print()

        PNet_WTagging_corr = Correction(
            name        = 'PNet_W_%stag'%('mis' if category=='ttbar' else ''),
            #script      = 'ParticleNetSFs/PNetMDWSF_weight.cc',
            script      = 'ParticleNetSFs/PNetMDWSF_weight.cc',
            constructor = [args.year, category, effpath, w_wp],
            mainFunc    = 'eval',
            corrtype    = 'weight',
            columnList  = ['Trijet_pt', 'Trijet_eta', 'Trijet_particleNetMD_WvsQCD', 'Trijet_GenMatchCats'],
        )
        selection.a.AddCorrection(
            correction = PNet_WTagging_corr,
            evalArgs   = {'pt':'Trijet_pt_corr', 'eta':'Trijet_eta', 'PNetWqq_score':'Trijet_particleNetMD_WvsQCD', 'jetCat':'Trijet_GenMatchCats'}
        )

        selection.a.DataFrame.Display(['PNet_W_%stag__nom'%('mis' if category=='ttbar' else '')]).Print()

    if not selection.a.isData:
        selection.a.DataFrame.Display(['genW__nom']).Print()
    # Having added the tagging and mistagging SFs to the appropriate processes, make uncertainty columns
    print('Tracking corrections: \n%s'%('\n\t- '.join(list(selection.a.GetCorrectionNames()))))
    kinOnly = selection.a.MakeWeightCols(
        correctionNames = list(selection.a.GetCorrectionNames()),
        extraNominal = '' if selection.a.isData else str(selection.GetXsecScale())
    )
    # Prepare a root file to save the templates
    if (args.njobs == 1):
        outFileName = f'rootfiles/XHYbbWWselection_{args.setname}_{args.year}%s.root'%('_'+args.variation if args.variation != 'None' else '')
    else:
        outFileName = f'rootfiles/XHYbbWWselection_{args.setname}_{args.year}%s_{args.ijob}of{args.njobs}.root'%('_'+args.variation if args.variation != 'None' else '')
    out = ROOT.TFile.Open(outFileName,'RECREATE')
    out.cd()
    # -----------------------------------------------------------------------------------------------------
    # Main SR/CR logic happens in this loop
    # -----------------------------------------------------------------------------------------------------
    cuts     = OrderedDict()
    PassFail = OrderedDict()

    for region in ['SR','CR']:
        print('-----------------------------------------------------------------------------------------------------')
        print(f'Selecting candidate %sWs in {region}...............'%('(anti-)' if 'CR' in region else ''))
        print('-----------------------------------------------------------------------------------------------------')
        selection.a.SetActiveNode(kinOnly)
        cuts[f'N_BEFORE_W_PICK_{region}'] = selection.getNweighted()
        objIdxs = f'ObjIdxs_{region}'

        # lower bound for CR Wtag inversion
        if 'CR' in region:
            lowerBound = 0.5 
        else:
            lowerBound = 0.123456   # not used for SR 

        selection.a.Define(
            objIdxs,
            'Pick_W_candidates_standard(%s, %s, %s, {0, 1, 2}, %s)'%(
                'Trijet_'+w_tagger,
                w_wp,
                'true' if region == 'CR' else 'false',
                lowerBound
            )
        )
        selection.a.Define(f'w1Idx','{}[0]'.format(objIdxs))
        selection.a.Define(f'w2Idx','{}[1]'.format(objIdxs))
        selection.a.Define(f'hIdx', '{}[2]'.format(objIdxs))
        selection.a.Cut('Has2Ws',f'(w1Idx > -1) && (w2Idx > -1) && (hIdx > -1)')
        cuts[f'N_AFTER_W_PICK_{region}'] = selection.getNweighted()
        # Perform the mass window cut in the SR
        if region == 'SR':
            mW1 = f'Trijet_mregressed_corr[w1Idx]'
            mW2 = f'Trijet_mregressed_corr[w2Idx]'
            window = [60.,110.]
            mWcut = f'({mW1} >= {window[0]}) && ({mW1} <= {window[1]}) && ({mW2} >= {window[0]}) && ({mW2} <= {window[1]})'
            selection.a.Cut('mW_window_cut',mWcut)
            cuts[f'N_AFTER_WMASS_CUT_{region}'] = selection.getNweighted()
        # At this point, rename Trijet -> W1/W2/Higgs based on its index determined above
        cols_to_skip = ['vect_msoftdrop','vect_mregressed','vect_msoftdrop_corr','vect_mregressed_corr','tau2','tau3','tau1','tau4','particleNetMD_QCD','deepTagMD_HbbvsQCD','particleNet_TvsQCD','particleNetMD_Xcc','deepTagMD_WvsQCD','particleNet_QCD','jetId','particleNetMD_Xbb','particleNet_WvsQCD','deepTagMD_ZHbbvsQCD','deepTag_TvsQCD','rawFactor','particleNetMD_Xqq']
        cols = ['Trijet_%s'%i for i in cols_to_skip]
        selection.a.ObjectFromCollection(f'W1','Trijet',f'w1Idx',skip=cols)
        selection.a.ObjectFromCollection(f'W2','Trijet',f'w2Idx',skip=cols)
        selection.a.ObjectFromCollection(f'H','Trijet',f'hIdx',skip=cols)
        # In order to avoid column naming duplicates, call these LeadW,SubleadW,Higgs
        selection.a.Define('LeadW_vect_softdrop','hardware::TLvector(W1_pt_corr, W1_eta, W1_phi, W1_msoftdrop_corr)')
        selection.a.Define('SubleadW_vect_softdrop','hardware::TLvector(W2_pt_corr, W2_eta, W2_phi, W2_msoftdrop_corr)')
        selection.a.Define('Higgs_vect_softdrop','hardware::TLvector(H_pt_corr, H_eta, H_phi, H_msoftdrop_corr)')
        # ------- regressed mass --------------
        selection.a.Define('LeadW_vect_regressed','hardware::TLvector(W1_pt_corr, W1_eta, W1_phi, W1_mregressed_corr)')
        selection.a.Define('SubleadW_vect_regressed','hardware::TLvector(W2_pt_corr, W2_eta, W2_phi, W2_mregressed_corr)')
        selection.a.Define('Higgs_vect_regressed','hardware::TLvector(H_pt_corr, H_eta, H_phi, H_mregressed_corr)')
        # make X and Y mass for both softdrop and regressed masses
        selection.a.Define('mhww_softdrop','hardware::InvariantMass({LeadW_vect_softdrop,SubleadW_vect_softdrop,Higgs_vect_softdrop})')
        selection.a.Define('mww_softdrop','hardware::InvariantMass({LeadW_vect_softdrop,SubleadW_vect_softdrop})')
        selection.a.Define('mhww_regressed','hardware::InvariantMass({LeadW_vect_regressed, SubleadW_vect_regressed, Higgs_vect_regressed})')
        checkpoint = selection.a.Define('mww_regressed','hardware::InvariantMass({LeadW_vect_regressed,SubleadW_vect_regressed})')
        # Now create pass/fail regions
        print(f'Defining Fail and Pass categories based on Higgs candidate score in {region}')
        for pf in ['fail','pass']: # without higgs mass cut
            selection.a.SetActiveNode(checkpoint)
            print(f'Tagging Higgs candidate in {region} {pf}....')
            # NOTE: "fail" is really just the former "loose" region.
            # Originally, we used:
            #   fail  : Hbb < 0.8
            #   loose : 0.8 < Hbb < 0.98
            #   pass  : Hbb > 0.98
            #
            # But now we just use Fail=Loose and Pass.
            if pf == 'fail': # really the "loose" region
                hCut = f'H_{h_tagger} >= 0.8 && H_{h_tagger} < {h_wp}'
            else:
                hCut = f'H_{h_tagger} >= {h_wp}'

            PassFail[f'{region}_{pf}'] = selection.a.Cut(f'{region}_{pf}_cut',hCut)
            cuts[f'N_AFTER_HIGGS_PICK_{region}_{pf}'] = selection.getNweighted()

        for pf in ['fail_mH_window','pass_mH_window']: # higgs regressed mass window cut
            selection.a.SetActiveNode(checkpoint)
            print(f'Tagging Higgs candidate in {region} {pf} with additional regressed mass window requirement...')
            if region == 'SR':
                mreg_cut = f'H_mregressed_corr >= 100 && H_mregressed_corr < 150'
            else:
                mreg_cut = f'(H_mregressed_corr >= 90 && H_mregressed_corr < 110) || (H_mregressed_corr >= 150 && H_mregressed_corr < 200)'
            selection.a.Cut(f'Higgs_mass_window_cut_{region}_{pf}',mreg_cut)
            hCut = f'H_{h_tagger} %s {h_wp}'%('>' if 'pass' in pf else '<')
            PassFail[f'{region}_{pf}'] = selection.a.Cut(f'{region}_{pf}_cut',hCut)
            cuts[f'N_AFTER_HIGGS_PICK_{region}_{pf}'] = selection.getNweighted()

    # We now have an ordered dict of pass/fail regions and the associated TIMBER nodes
    # We will use this to construct 2D templates for each region and systematic variation
    binsX = [45,0,4500]
    binsY = [35,0,3500]
    for pf_region, node in PassFail.items():
        print(f'Generating 2D template for region {pf_region}.......')
        selection.a.SetActiveNode(node)
        templates = selection.a.MakeTemplateHistos(
            ROOT.TH2F(
                f'MXvMY_{pf_region}', f'MX vs MY {pf_region}',
                binsX[0], binsX[1], binsX[2],
                binsY[0], binsY[1], binsY[2]
            ),
            ['mhww_softdrop','mww_softdrop']
        )
        templates.Do('Write')
    # Save out cutflow information
    hCutflow = ROOT.TH1F('cutflow','Number of events after each cut',len(cuts),0.5,len(cuts)+0.5)
    nBin = 1
    for cutname, cutval  in cuts.items():
        print(f'Obtaining cutflow for {cutname}')
        nCut = cutval.GetValue()
        print(f'\t{cutname} = {nCut}')
        hCutflow.GetXaxis().SetBinLabel(nBin, cutname)
        hCutflow.AddBinContent(nBin, nCut)
        nBin += 1
    print('Writring cutflow histogram to file')
    hCutflow.Write()
    out.Close()
    print('Script finished')


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
                        action='store', required=True,
                        help='Setname to process.')
    parser.add_argument('-y', type=str, dest='year',
                        action='store', required=True,
                        help='Year of set (16, 17, 18).')
    parser.add_argument('-v', type=str, dest='variation',
                        action='store', default='None',
                        help='JES_up, JES_down, JMR_up,...')
    # FOR DEBUGGING
    parser.add_argument('-n', type=int, dest='njobs',
                        action='store', default='1',
                        help='Number of jobs to split the total files into')
    parser.add_argument('-j', type=int, dest='ijob',
                        action='store', default=1,
                        help='Which job to run on')
    parser.add_argument('--verbose', dest='verbose',
                        action='store_true', help='Enable RDF verbosity')

    args = parser.parse_args()
    if args.verbose:
        verbosity = ROOT.Experimental.RLogScopedVerbosity(ROOT.Detail.RDF.RDFLogChannel(), ROOT.Experimental.ELogLevel.kDebug+10)

    if ('Data' not in args.setname):
        trigyear = args.year if 'APV' not in args.setname else '16'
        args.trigEff = Correction(
            name        = f'TriggerEff{trigyear}',
            script      = 'TIMBER/Framework/include/EffLoader.h',
            constructor = [f'triggers/HWWtrigger2D_HT0_{trigyear}.root', 'Pretag'],
            corrtype    = 'weight'
        )
    else:
        args.trigEff = None
    CompileCpp('HWWmodules.cc')
    selection(args)
