import ROOT, time
from TIMBER.Analyzer import HistGroup, Correction, Node
from TIMBER.Tools.Common import CompileCpp
from collections import OrderedDict
import TIMBER.Tools.AutoJME as AutoJME
from XHYbbWW_class import XHYbbWW
from memory_profiler import profile

@profile
def selection(args):
    print(f'Processing {args.setname} {args.year} for selection and 2D histogram creation.....')
    start = time.time()
    selection = XHYbbWW(f'trijet_nano/{args.setname}_{args.year}_snapshot.txt',args.year,int(args.ijob),int(args.njobs))
    selection.OpenForSelection(args.variation)
    selection.ApplyTrigs(args.trigEff)

    # Apply tagging (signal) or mistagging (ttbar) scale factors
    eosdir  = 'root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/TaggerEfficiencies'
    effpath = f'{eosdir}/{args.setname}_{args.year}_Efficiencies.root'
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
            name        = 'PNetMD_Hbb_tag',
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

        selection.a.DataFrame.Display(['PNetMD_Hbb_tag__nom']).Print()

        PNet_WTagging_corr = Correction(
            name        = 'PNet_W_tag',
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

        selection.a.DataFrame.Display(['PNet_W_tag__nom']).Print()

    selection.a.DataFrame.Display(['genW__nom']).Print()
    # Having added the tagging and mistagging SFs to the appropriate processes, make uncertainty columns
    print('Tracking corrections: \n%s'%('\n\t- '.join(list(selection.a.GetCorrectionNames()))))
    kinOnly = selection.a.MakeWeightCols(
        correctionNames = list(selection.a.GetCorrectionNames()),
        extraNominal = '' if selection.a.isData else str(selection.GetXsecScale())
    )

    # save all of the weight columns
    corrs = list(selection.a.GetCorrectionNames())
    cols = []
    for corr in corrs:
        if corr == 'genW': continue
        for var in ['nom','up','down']:
            cols.append(f'{corr}__{var}')           # the individual correction
            cols.append(f'weight__{corr}_{var}')    # the weight column calculated by MakeWeightCols()
    cols.append('weight__nominal')
    selection.a.Snapshot(cols,f'TEST_PNET_SYSTS_{args.setname}_{args.year}.root','Events')


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
    parser.add_argument('--plot', dest='plot',
                        action='store_true', help='Plot the template uncertainty histograms')

    args = parser.parse_args()
    if args.verbose:
        verbosity = ROOT.Experimental.RLogScopedVerbosity(ROOT.Detail.RDF.RDFLogChannel(), ROOT.Experimental.ELogLevel.kDebug+10)
    if ('Data' not in args.setname):
        trigyear = args.year if 'APV' not in args.setname else '16'
        args.trigEff = Correction(
            name        = f'TriggerEff{trigyear}',
            script      = 'TIMBER/Framework/include/EffLoader.h',
            constructor = ['triggers/HWWtrigger2D_HT0_17B.root', 'Pretag'],
            corrtype    = 'weight'
        )
    CompileCpp('HWWmodules.cc')
    selection(args)
