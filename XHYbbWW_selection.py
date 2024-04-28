import ROOT, time
from TIMBER.Analyzer import HistGroup, Correction, Node
from TIMBER.Tools.Common import CompileCpp
from collections import OrderedDict
import TIMBER.Tools.AutoJME as AutoJME
from XHYbbWW_class import XHYbbWW
#from memory_profiler import profile
from multiprocessing import Process, Queue

def ranges(num_entries, chunks):
    chunks = int(chunks)
    step = num_entries / chunks
    l_out = [[round(step*i),round(step*(i+1))] for i in range(chunks)]
    # get remainder
    nMinus1 = l_out[-1][-1]
    if nMinus1 == num_entries:
        return l_out
    else:
        final_chunk = [nMinus1, num_entries]
        l_out.append(final_chunk)
        return l_out

def selection(args):
    print('PROCESSING: {} {}'.format(args.setname, args.year))
    start = time.time()

    selection = XHYbbWW('trijet_nano/{}_{}_snapshot.txt'.format(args.setname,args.year),args.year,1,1)

    if args.nchunks == 'all':
        outFileName = 'rootfiles/XHYbbWWselection_HT{}_{}_{}{}.root'.format(args.HT, args.setname, args.year, '_'+args.variation if args.variation != 'None' else '')
    else:
        assert(int(args.ijob) < int(args.nchunks))
        nEntries = selection.a.DataFrame.Count().GetValue()
        chunk_ranges = ranges(nEntries, int(args.nchunks))
        chunk = chunk_ranges[args.ijob]
        print('Running only on events %s-%s'%(chunk[0],chunk[-1]))
        small_rdf = selection.a.GetActiveNode().DataFrame.Range(chunk[0],chunk[-1])
        small_node = Node('chunk_%s-%s'%(chunk[0],chunk[-1]),small_rdf)
        selection.a.SetActiveNode(small_node)
        outFileName = 'rootfiles/XHYbbWWselection_HT{}_{}_{}{}_CHUNK{}.root'.format(args.HT, args.setname, args.year, '_'+args.variation if args.variation != 'None' else '',args.ijob)

    selection.OpenForSelection(args.variation) # automatically applies corrections

    # Apply HT cut due to improved trigger effs (OUTDATED, HT CUT SHOULD ALWAYS BE ZERO)
    selection.a.Cut('HT_cut','HT > {}'.format(args.HT))

    # Apply trigger efficiencies
    selection.ApplyTrigs(args.trigEff)

    # Tagger defintions and WPs
    w_tagger = 'particleNetMD_WvsQCD'
    w_wp = 0.8
    h_tagger = 'particleNetMD_HbbvsQCD'
    h_wp = 0.98

    ########################################################################################################################
    # Logic to determine whether to apply (mis)tagging SFs to pick the H/W/W candidates or just use the raw tagging scores #
    ########################################################################################################################
    if ('NMSSM' in args.setname) or ('ttbar' in args.setname):
        # Code to perform gen matching
        CompileCpp('ParticleNetSFs/TopMergingFunctions.cc')
        # The classes implemented in these files will apply PNet tagging factors to signal
        # and mistagging SFs to ttbar MC in order to perform the H/W/W selection. For data
        # and other MC processes, the functions in HWWmodules.cc will perform the same
        # selection, using just the raw tagger scores instead.
        CompileCpp('ParticleNetSFs/PNetWqqSFHandler.cc')
        CompileCpp('ParticleNetSFs/PNetHbbSFHandler.cc')
        # Perform gen matching to each of the three candidate jets to determine H/W or top(merging) status of each
        # By prepending 'Trijet_' to the name, it will get picked up by TIMBER.Analyzer.SubCollection() and we can
        # then save the gen matching category status alongside any H/W/W candidates produced later.
        selection.a.Define('Trijet_GenMatchCats','classifyProbeJets({0,1,2}, Trijet_phi, Trijet_eta, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother)')
        # Determine which variations should be applied
        if 'NMSSM' in args.setname:   category = 'signal'
        elif 'ttbar' in args.setname: category = 'ttbar'
        else: category = 'other'    # will not happen here 
        if (category != 'other'):
            if (args.variation == 'PNetHbb_up'):
                HbbVar = 1  # vary Hbb (mis)tag SFs up
                WqqVar = 0  # keep Wqq (mis)tag SFs nominal
            elif (args.variation == 'PNetHbb_down'):
                HbbVar = 2  # vary Hbb (mis)tag SFs down
                WqqVar = 0  # keep Wqq (mis)tag SFs nominal
            elif (args.variation == 'PNetWqq_up'):
                HbbVar = 0  # keep Hbb (mis)tag SFs nominal
                WqqVar = 1  # vary Wqq (mis)tag SFs up
            elif (args.variation == 'PNetWqq_down'):
                HbbVar = 0  # keep Hbb (mis)tag SFs nominal
                WqqVar = 2  # vary Wqq (mis)tag SFs up
            else:
                HbbVar = 0  # keep both (mis)tag SFs nominal
                WqqVar = 0
        # Path to efficiency file
        effpath = 'ParticleNetSFs/EfficiencyMaps/%s_%s_Efficiencies.root'%(args.setname, args.year)
        # Instantiate the PNet SF helpers. This is mandatory, even for non-signal/ttbar processes.
        # They will automatically handle the application of (mis)tagging SFs to (ttbar)signal processes, and will apply
        # normal H/W/W selection otherwise.
        WqqSFHandler_args = 'PNetWqqSFHandler WqqSFHandler = PNetWqqSFHandler("%s", "%s", "%s", %f, 12345);'%(args.year, category, effpath, w_wp)
        HbbSFHandler_args = 'PNetHbbSFHandler HbbSFHandler = PNetHbbSFHandler("%s", "%s", "%s", %f, 12345);'%(args.year, category, effpath, h_wp)
        print('Instantiating PNetWqqSFHandler object:\n\t%s'%WqqSFHandler_args)
        CompileCpp(WqqSFHandler_args)
        print('Instantiating PNetHbbSFHandler object:\n\t%s'%HbbSFHandler_args)
        CompileCpp(HbbSFHandler_args)


    else:
        # Define variables here so script doesn't complain later
        category = 'other'
        HbbVar = 0
        WqqVar = 0
        # Used to pick Ws, H for non-ttbar/signal files (V+jets, data, single-top, etc)
        CompileCpp('HWWmodules.cc')

    # Create a checkpoint with the proper event weights
    kinOnly = selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else str(selection.GetXsecScale()))

    # Prepare a root file to save the templates
    out = ROOT.TFile.Open(outFileName, 'RECREATE')
    out.cd()

    # Now define the SR and CR
    for region in ['SR', 'CR']:	# here, CR really represents the QCD control region used for making SR toys.
        print('------------------------------------------------------------------------------------------------')
        print('				Performing selection in %s'%region)
        print('------------------------------------------------------------------------------------------------')
        selection.a.SetActiveNode(kinOnly)
        print('Selecting candidate %sWs in %s...'%('(anti-)' if region == 'CR' else '', region))
        # NOTE: it is important to pass in dummy vector for the genMatch categories for any non-signal/ttbar processes.
        selection.Pick_W_candidates(
                SRorCR           = region,
                WqqSFHandler_obj = 'WqqSFHandler',                      # instance of the Wqq SF handler class
                Wqq_discriminant = 'Trijet_particleNetMD_WvsQCD',       # raw MD_WvsQCD tagger score from PNet
                corrected_pt     = 'Trijet_pt_corr',                    # corrected pt
                trijet_eta       = 'Trijet_eta',                        # eta
                corrected_mass   = 'Trijet_mregressed_corr',            # corrected softdrop mass for mass window req
                genMatchCats     = 'Trijet_GenMatchCats' if category != 'other' else '{-1,-1,-1}', # gen matching jet cats from `TopMergingFunctions.cc`
                Wqq_variation    = WqqVar,                              # 0: nominal, 1: up, 2:down
                invert           = False if region == 'SR' else True,   # False: SR, True: CR
                mass_window      = [60., 110.]                          # W mass window for selection of W cands
        )
        # At this point we will have identified the two (anti-)W candidates and the Higgs candidate (by proxy).
        # The above method defines new TIMBER SubCollections for the H/W/W candidates using H, W1, W2 as prefixes.
        # We must now apply the pass and fail Hbb tagging cuts to create the signal and control regions for the final search.

        #print(selection.a.DataFrame.Sum("genWeight").GetValue())
        #print(selection.a.DataFrame.Display("ObjIdxs_%s"%region,100).Print())
        #print(selection.a.DataFrame.Display('Trijet_pt_corr',1).Print())
        #print(selection.a.DataFrame.Display('nGenPart',15).Print())
        #print(selection.a.DataFrame.Display('w1Idx',15).Print())
        #print(selection.a.DataFrame.Display('w2Idx',15).Print())
        #print(selection.a.DataFrame.Display('hIdx',15).Print())
        #selection.a.Cut("test_hIdx_cut","hIdx>=0")
        #selection.a.DataFrame.Sum("genWeight").GetValue()


        print('Defining Fail and Pass categories based on Higgs candidate score in %s...'%region)
        # NOTE: it is important to pass in dummy value for the GenMatch category for any non-signal/ttbar processes
        PassFail = selection.ApplyHiggsTag(
            SRorCR           = region,
            HbbSFHandler_obj = 'HbbSFHandler',
            Hbb_discriminant = 'H_particleNetMD_HbbvsQCD',
            corrected_pt     = 'H_pt_corr',
            jet_eta          = 'H_eta',
            corrected_mass   = 'H_mregressed_corr',
            genMatchCat      = 'H_GenMatchCats' if category != 'other' else '-1',
            Hbb_variation    = HbbVar,
            invert           = False if region == 'SR' else True,
            mass_window      = [110., 145.]
        )

        #print(selection.a.DataFrame.Display("HiggsTagStatus", 10).Print())
        #selection.a.DataFrame.Sum("genWeight").GetValue()


        # We now have an ordered dictionary of Pass/Fail regions and the associated TIMBER nodes. We will use this 
        # to construct the 2D templates for each region and systematic variation.
        binsX = [45, 0, 4500]
        binsY = [35, 0, 3500]
        for pf_region, node in PassFail.items():
            print('Generating 2D templates for region %s...'%pf_region)
            # The node will have columns for mX and mY calculated with both softdrop and regressed masses (both corrected).
            # We will only use the softdrop 4-vectors for the invariant masses (as per JMAR).
            for mass in ['softdrop']:
                mod_name  = '%s_%s_m%s'%(region, pf_region, mass)
                mod_title = '%s %s %s'%(region, pf_region, mass)
                selection.a.SetActiveNode(node)
                print('\tEvaluating %s'%(mod_title))
                mX = 'mhww_%s'%mass
                mY = 'mww_%s'%mass
                templates = selection.a.MakeTemplateHistos(ROOT.TH2F('MXvMY_%s'%mod_name, 'MXvMY %s with %s'%(mod_title,'particleNet'),binsX[0],binsX[1],binsX[2],binsY[0],binsY[1],binsY[2]),[mX,mY])
                templates.Do('Write')

    # Save out cutflow information from selection
    cuts = ['NBEFORE_W_PICK_SR','NBEFORE_W_PICK_CR','NAFTER_W_PICK_SR','NAFTER_W_PICK_CR','NAFTER_W_MASS_REQ_SR','NBEFORE_H_PICK_SR','NBEFORE_H_PICK_CR','NAFTER_H_PICK_SR_FAIL','NAFTER_H_PICK_SR_PASS','NAFTER_H_PICK_CR_FAIL','NAFTER_H_PICK_CR_PASS','NAFTER_H_PICK_SR_FAIL_MHCUT','NAFTER_H_PICK_SR_PASS_MHCUT','NAFTER_H_PICK_CR_FAIL_MHCUT','NAFTER_H_PICK_CR_FAIL_MHCUT']
    hCutflow = ROOT.TH1F('cutflow', 'Number of events after each cut', len(cuts), 0.5, len(cuts)+0.5)
    nBin = 1
    for cut in cuts:
        print('Obtaining cutflow for %s'%cut)
        nCut = getattr(selection, cut).GetValue()
        print('\t%s \t= %s'%(cut,nCut))
        hCutflow.GetXaxis().SetBinLabel(nBin, cut)
        hCutflow.AddBinContent(nBin, nCut)
        nBin += 1
    hCutflow.Write()

    # Done!
    out.Close()

if __name__ == '__main__':
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
    parser.add_argument('--HT', type=str, dest='HT',
                        action='store', default='0',
                         help='Value of HT to cut on')
    # FOR DEBUGGING
    parser.add_argument('-n', type=str, dest='nchunks',
			action='store', default='all',
			help='Number of chunks to split the total dataframe into (for debugging memory usage)')
    parser.add_argument('-j', type=int, dest='ijob',
                        action='store', default=0,
                        help='Which chunk to run on')


    args = parser.parse_args()

    #verbosity = ROOT.Experimental.RLogScopedVerbosity(ROOT.Detail.RDF.RDFLogChannel(), ROOT.Experimental.ELogLevel.kDebug+10)

    # We must apply the 2017B triffer efficiency to ~12% of the 2017 MC
    # This trigEff correction is passed to ApplyTrigs() in the XHYbbWW_selection() function
    if ('Data' not in args.setname) and (args.year == '17'): # we are dealing with MC from 2017
        cutoff = 0.11283 # fraction of total JetHT data belonging to 2017B (11.283323383%)
        TRand = ROOT.TRandom3()
        rand = TRand.Uniform(0.0, 1.0)
        if rand < cutoff:
            print('Applying 2017B trigger efficiency')
            args.trigEff = Correction("TriggerEff17",'TIMBER/Framework/include/EffLoader.h',['triggers/HWWtrigger2D_HT{}_17B.root'.format(args.HT),'Pretag'],corrtype='weight')
        else:
            args.trigEff = Correction("TriggerEff17",'TIMBER/Framework/include/EffLoader.h',['triggers/HWWtrigger2D_HT{}_17.root'.format(args.HT),'Pretag'],corrtype='weight')
    else:
        args.trigEff = Correction("TriggerEff"+args.year,'TIMBER/Framework/include/EffLoader.h',['triggers/HWWtrigger2D_HT{}_{}.root'.format(args.HT,args.year if 'APV' not in args.year else 16),'Pretag'], corrtype='weight')

    selection(args)
