import ROOT, time
from TIMBER.Analyzer import HistGroup, Correction, Node
from TIMBER.Tools.Common import CompileCpp, ExecuteCmd
from collections import OrderedDict
import TIMBER.Tools.AutoJME as AutoJME
from XHYbbWW_class import XHYbbWW

Wqq_WPs = {
    '16APV': 0.637,
    '16': 0.642,
    '17': 0.579,
    '18': 0.59
}

def selection(args):
    print(f'Processing {args.setname} {args.year} for selection and 2D histogram creation.....')
    start = time.time()

    # Prepare a dictionary to store cutflow 
    cuts = OrderedDict()

    # Basic selection and corrections applied to all processes    
    selection = XHYbbWW(f'trijet_nano/{args.setname}_{args.year}_snapshot.txt',args.year,int(args.ijob),int(args.njobs))
    cuts['n_start'] = selection.getNweighted()

    selection.OpenForSelection(args.variation, runCorrs=True)
    selection.ApplyTrigs(args.trigEff)
    cuts['n_after_corrections'] = selection.getNweighted()

    # Apply tagging (signal) or mistagging (ttbar) scale factors 
    eosdir  = 'root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/TaggerEfficiencies'
    eospath = f'{eosdir}/{args.setname}_{args.year}_Efficiencies.root'
    effpath = f'ParticleNetSFs/EfficiencyMaps/{args.setname}_{args.year}_Efficiencies.root'
    if ('ttbar' in args.setname) or ('NMSSM' in args.setname):
        # Copy the file locally so we don't have to worry about xrootd latency
        ExecuteCmd(f'xrdcp {eospath} ./ParticleNetSFs/EfficiencyMaps/')
        # Constants
        w_tagger = 'particleNetMD_WvsQCD'
        h_tagger = 'particleNetMD_HbbvsQCD'
        w_wp = Wqq_WPs[args.year]
        h_wp = 0.98
        # Compile helper functions
        CompileCpp('ParticleNetSFs/TopMergingFunctions.cc')
        selection.a.Define('Trijet_GenMatchCats','classifyProbeJets({0,1,2}, Trijet_phi, Trijet_eta, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother)')
        # Pass the category to the constructor so the class can use tagging or mistagging systematics automatically
        category = 'ttbar' if 'ttbar' in args.setname else 'signal'
        PNet_HbbTagging_corr = Correction(
            name        = 'PNetMD_Hbb_%stag'%('mis' if category=='ttbar' else ''),
            script      = 'ParticleNetSFs/PNetXbbSF_weight.cc',
            constructor = [args.year, category, effpath, h_wp],
            mainFunc    = 'eval_tag' if category == 'signal' else 'eval_mistag',
            corrtype    = 'weight',
            columnList  = ['Trijet_pt_corr', 'Trijet_eta', 'Trijet_particleNetMD_HbbvsQCD', 'Trijet_GenMatchCats']
        )
        selection.a.AddCorrection(
            correction  = PNet_HbbTagging_corr,
            evalArgs    = {'pt':'Trijet_pt_corr', 'eta':'Trijet_eta', 'PNetXbb_score':'Trijet_particleNetMD_HbbvsQCD', 'jetCat':'Trijet_GenMatchCats'}
        )

        #selection.a.DataFrame.Display(['PNetMD_Hbb_%stag__nom'%('mis' if category=='ttbar' else '')]).Print()

        PNet_WTagging_corr = Correction(
            name        = 'PNet_W_%stag'%('mis' if category=='ttbar' else ''),
            script      = 'ParticleNetSFs/PNetMDWSF_weight.cc',
            constructor = [args.year, category, effpath, w_wp],
            mainFunc    = 'eval_tag' if category == 'signal' else 'eval_mistag',
            corrtype    = 'weight',
            columnList  = ['Trijet_pt', 'Trijet_eta', 'Trijet_particleNetMD_WvsQCD', 'Trijet_GenMatchCats'],
        )
        selection.a.AddCorrection(
            correction = PNet_WTagging_corr,
            evalArgs   = {'pt':'Trijet_pt_corr', 'eta':'Trijet_eta', 'PNetWqq_score':'Trijet_particleNetMD_WvsQCD', 'jetCat':'Trijet_GenMatchCats'}
        )

        #selection.a.DataFrame.Display(['PNet_W_%stag__nom'%('mis' if category=='ttbar' else '')]).Print()




    # Perform H,W1,W2 candidate selection the same way for both SR/VR
    selection.a.Define(f'Higgs_candidate_idx','Pick_H_candidate(Trijet_particleNetMD_HbbvsQCD,{0,1,2})')
    selection.a.Define(f'DummyW_idx0',f'Higgs_candidate_idx[1]') # the 0th index belongs to Higgs candidate 
    selection.a.Define(f'DummyW_idx1',f'Higgs_candidate_idx[2]') # the 0th index belongs to Higgs candidate
    selection.a.Define(f'W_candidate_idxs','Pick_W_candidates(Trijet_particleNetMD_WvsQCD, %s, {DummyW_idx0, DummyW_idx1})'%(Wqq_WPs[args.year]))
    selection.a.Define(f'H_idx',f'Higgs_candidate_idx[0]')
    selection.a.Define(f'W1_idx',f'W_candidate_idxs[0]')
    selection.a.Define(f'W2_idx',f'W_candidate_idxs[1]')
    selection.a.Cut(f'Has2Ws',f'(W1_idx >= 0) && (W2_idx >= 0)')
    cuts[f'n_after_Has2Ws'] = selection.getNweighted()

    # Create collections and TLVectors
    cols_to_skip = ['vect_msoftdrop','vect_particleNet_mass','vect_msoftdrop_corr','vect_particleNet_mass','tau2','tau3','tau1','tau4','particleNetMD_QCD','deepTagMD_HbbvsQCD','particleNet_TvsQCD','particleNetMD_Xcc','deepTagMD_WvsQCD','particleNet_QCD','jetId','particleNetMD_Xbb','particleNet_WvsQCD','deepTagMD_ZHbbvsQCD','deepTag_TvsQCD','rawFactor','particleNetMD_Xqq']
    cols = ['Trijet_%s'%i for i in cols_to_skip]
    selection.a.ObjectFromCollection(f'H','Trijet',f'H_idx',skip=cols)
    selection.a.ObjectFromCollection(f'W1','Trijet',f'W1_idx',skip=cols)
    selection.a.ObjectFromCollection(f'W2','Trijet',f'W2_idx',skip=cols)
    selection.a.Define(f'Higgs_vect',    f'hardware::TLvector(H_pt_corr, H_eta, H_phi, H_mregressed_corr)')
    selection.a.Define(f'LeadW_vect',    f'hardware::TLvector(W1_pt_corr, W1_eta, W1_phi, W1_mregressed_corr)')
    selection.a.Define(f'SubleadW_vect', f'hardware::TLvector(W2_pt_corr, W2_eta, W2_phi, W2_mregressed_corr)')
    selection.a.Define(f'mhww','hardware::InvariantMass({LeadW_vect, SubleadW_vect, Higgs_vect})')
    selection.a.Define(f'mww','hardware::InvariantMass({LeadW_vect, SubleadW_vect})')

    # Apply W mass cuts
    mW1 = f'W1_mregressed_corr'
    mW2 = f'W2_mregressed_corr'
    window = [60., 110.]
    mW_cut = f'({mW1} >= {window[0]}) && ({mW1} <= {window[1]}) && ({mW2} >= {window[0]}) && ({mW2} <= {window[1]})'
    selection.a.Cut(f'mW_window_cut',mW_cut)
    cuts[f'n_after_WmassCut'] = selection.getNweighted()


    # Having added the tagging and mistagging SFs to the appropriate processes, make uncertainty cols
    print('Tracking corrections:\n\t%s'%("\n\t- ".join(list(selection.a.GetCorrectionNames()))))

    # EXPERIMENTAL
    uncerts_to_corr = {}

    VRSR_CHECKPOINT = selection.a.MakeWeightCols(
        correctionNames = list(selection.a.GetCorrectionNames()),
        uncerts_to_corr=uncerts_to_corr,
        extraNominal = '' if selection.a.isData else f'{selection.GetXsecScale()}'
    )

    # Prepare a root file to save the templates
    if (args.njobs == 1):
        outFileName = f'rootfiles/XHYbbWWselection_{args.setname}_{args.year}%s.root'%('_'+args.variation if args.variation != 'None' else '')
    else:
        outFileName = f'rootfiles/XHYbbWWselection_{args.setname}_{args.year}%s_{args.ijob}of{args.njobs}.root'%('_'+args.variation if args.variation != 'None' else '')
    out = ROOT.TFile.Open(outFileName,'RECREATE')
    out.cd()

    PassFail = OrderedDict()

    '''
    Main SR/VR logic happens in the following loop
    We have now selected:
        - one H candidate based on leading Hbb score
        - two W candidates with Wqq score and W mass requirements
    Now we can begin the creation of VR and SR, which differ only by the Hbb mass req
        - VR : [75, 100) || (150, 175] GeV
        - SR : [100, 150] GeV
    Both use identical Fail/Pass Hbb score requirements
    '''
    for region in ['VR','SR']:
        print(f'-----------------------------------------------------------------')
        print(f'Creating {region} with corresponding mass window requirement')
        print(f'-----------------------------------------------------------------')
        selection.a.SetActiveNode(VRSR_CHECKPOINT)

        if region == 'SR':
            # Higgs mass window
            cutval = f'(H_mregressed_corr >= 100) && (H_mregressed_corr <= 150)'
        else: 
            # Higgs mass sidebands
            cutval = f'((H_mregressed_corr >= 75) && (H_mregressed_corr < 100)) || ((H_mregressed_corr > 150) && (H_mregressed_corr <= 175))'

        cutname = f'{region}_Hbb_mass_cut'
        PF_CHECKPOINT = selection.a.Cut(cutname,cutval)
        cuts[f'n_after_{region}_HbbMassCut'] = selection.getNweighted()

        # Now create Fail and Pass based on Hbb score cut 
        for pf in ['fail','pass']:
            print(f'-----------------------------------------------------------------')
            print(f'Creating {region} {pf} with corresponding Hbb score requirement  ')
            print(f'-----------------------------------------------------------------')
            selection.a.SetActiveNode(PF_CHECKPOINT)
            print(f'\tSwitched to node {PF_CHECKPOINT.name}')
            if pf == 'pass':
                cutVal = f'H_particleNetMD_HbbvsQCD >= 0.98'
            else:
                cutVal = f'H_particleNetMD_HbbvsQCD < 0.98'
            cutname = f'{region}_{pf}_HbbCut'
            PassFail[f'{region}_{pf}'] = selection.a.Cut(cutname,cutVal)
            cuts[f'n_after_{region}_{pf}_HbbScoreCut'] = selection.getNweighted()

    '''
    We now have an ordered dict of fail/pass regions and the associated TIMBER nodes.
    We will use this to construct 2D templates for each region and systmatic variation.
    '''
    binsX = [45,0,4500]
    binsY = [45,0,4500]
    for pf_region, node in PassFail.items():
        print(f'Generating 2D template for region {pf_region}......')
        selection.a.SetActiveNode(node)
        templates = selection.a.MakeTemplateHistos(
            ROOT.TH2F(
                f'MXvsMY_{pf_region}', f'MX vs MY {pf_region}',
                binsX[0], binsX[1], binsX[2],
                binsY[0], binsY[1], binsY[2]
            ),
            ['mhww','mww']
        )
        print(templates)
        templates.Do('Write')

    # Save out the cutflow information 
    hCutflow = ROOT.TH1F('cutflow','Number of events after each cut',len(cuts),0.5,len(cuts)+0.5)
    nBin = 1
    nBin = 1
    for cutname, cutval  in cuts.items():
        print(f'Obtaining cutflow for {cutname}')
        nCut = cutval.GetValue()
        print(f'\t{cutname} = {nCut}')
        hCutflow.GetXaxis().SetBinLabel(nBin, cutname)
        hCutflow.AddBinContent(nBin, nCut)
        nBin += 1
    print('Writing cutflow histogram to file')
    hCutflow.Write()
    out.Close()

    ExecuteCmd(f'rm ParticleNetSFs/EfficiencyMaps/{args.setname}_{args.year}_Efficiencies.root')

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
        #trigyear = args.year if 'APV' not in args.setname else '16'
        if 'APV' in args.year:
            trigyear = '16'
        else:
            trigyear = args.year
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
