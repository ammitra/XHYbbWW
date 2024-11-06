import ROOT, time
from TIMBER.Analyzer import HistGroup, Correction, Node
from TIMBER.Tools.Common import CompileCpp
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

    columns = ['H_JES__vec', 'H_JES__vecT', 'H_JES_nom', 'H_JES_up', 'H_JES_down', 'H_JER__vec', 'H_JER__vecT', 'H_JER_nom', 'H_JER_up', 'H_JER_down', 'H_JMS_softdrop__vec', 'H_JMS_softdrop__vecT', 'H_JMS_softdrop_nom', 'H_JMS_softdrop_up', 'H_JMS_softdrop_down', 'H_JMR_softdrop__vec', 'H_JMR_softdrop__vecT', 'H_JMR_softdrop_nom', 'H_JMR_softdrop_up', 'H_JMR_softdrop_down', 'H_JMS_regressed__vec', 'H_JMS_regressed__vecT', 'H_JMS_regressed_nom', 'H_JMS_regressed_up', 'H_JMS_regressed_down', 'H_JMR_regressed__vec', 'H_JMR_regressed__vecT', 'H_JMR_regressed_nom', 'H_JMR_regressed_up', 'H_JMR_regressed_down', 'H_vect_mregressed', 'H_pt_corr', 'H_msoftdrop_corr', 'H_mregressed_corr', 'H_vect_mregressed_corr', 'H_area', 'H_eta', 'H_mass', 'H_msoftdrop', 'H_particleNet_HbbvsQCD', 'H_particleNet_mass', 'H_phi', 'H_pt', 'H_subJetIdx1', 'H_subJetIdx2', 'H_genJetAK8Idx', 'W1_particleNetMD_WvsQCD', 'W1_particleNetMD_HbbvsQCD',  'W1_JES__vec', 'W1_JES__vecT', 'W1_JES_nom', 'W1_JES_up', 'W1_JES_down', 'W1_JER__vec', 'W1_JER__vecT', 'W1_JER_nom', 'W1_JER_up', 'W1_JER_down', 'W1_JMS_softdrop__vec', 'W1_JMS_softdrop__vecT', 'W1_JMS_softdrop_nom', 'W1_JMS_softdrop_up', 'W1_JMS_softdrop_down', 'W1_JMR_softdrop__vec', 'W1_JMR_softdrop__vecT', 'W1_JMR_softdrop_nom', 'W1_JMR_softdrop_up', 'W1_JMR_softdrop_down', 'W1_JMS_regressed__vec', 'W1_JMS_regressed__vecT', 'W1_JMS_regressed_nom', 'W1_JMS_regressed_up', 'W1_JMS_regressed_down', 'W1_JMR_regressed__vec', 'W1_JMR_regressed__vecT', 'W1_JMR_regressed_nom', 'W1_JMR_regressed_up', 'W1_JMR_regressed_down', 'W1_vect_mregressed', 'W1_pt_corr', 'W1_msoftdrop_corr', 'W1_mregressed_corr', 'W1_vect_mregressed_corr', 'W1_area', 'W1_eta', 'W1_mass', 'W1_msoftdrop', 'W1_particleNet_HbbvsQCD', 'W1_particleNet_mass', 'W1_phi', 'W1_pt', 'W1_subJetIdx1', 'W1_subJetIdx2', 'W1_genJetAK8Idx', 'W2_particleNetMD_WvsQCD', 'W2_particleNetMD_HbbvsQCD',  'W2_JES__vec', 'W2_JES__vecT', 'W2_JES_nom', 'W2_JES_up', 'W2_JES_down', 'W2_JER__vec', 'W2_JER__vecT', 'W2_JER_nom', 'W2_JER_up', 'W2_JER_down', 'W2_JMS_softdrop__vec', 'W2_JMS_softdrop__vecT', 'W2_JMS_softdrop_nom', 'W2_JMS_softdrop_up', 'W2_JMS_softdrop_down', 'W2_JMR_softdrop__vec', 'W2_JMR_softdrop__vecT', 'W2_JMR_softdrop_nom', 'W2_JMR_softdrop_up', 'W2_JMR_softdrop_down', 'W2_JMS_regressed__vec', 'W2_JMS_regressed__vecT', 'W2_JMS_regressed_nom', 'W2_JMS_regressed_up', 'W2_JMS_regressed_down', 'W2_JMR_regressed__vec', 'W2_JMR_regressed__vecT', 'W2_JMR_regressed_nom', 'W2_JMR_regressed_up', 'W2_JMR_regressed_down', 'W2_vect_mregressed', 'W2_pt_corr', 'W2_msoftdrop_corr', 'W2_mregressed_corr', 'W2_vect_mregressed_corr', 'W2_area', 'W2_eta', 'W2_mass', 'W2_msoftdrop', 'W2_particleNet_HbbvsQCD', 'W2_particleNet_mass', 'W2_phi', 'W2_pt', 'W2_subJetIdx1', 'W2_subJetIdx2', 'W2_genJetAK8Idx', 'Higgs_vect', 'LeadW_vect', 'SubleadW_vect', 'mhww', 'mww']

    selection.a.Snapshot(columns, 'rootfiles/DEBUG_{}_{}.root'.format(args.setname,args.year),'Events', openOption='RECREATE',saveRunChain=True)


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
