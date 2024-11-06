'''
Studies on gen matching to understand poor signal reconstruction

Histogram naming keys:
    - SR0,1,2 correspond to SRs using loose,medium,tight MD_WvsQCD WP
    - PRETAG refers to pre-tag distributions
    - stage1 refers to distributions *before* W mass cut 
    - stage2 refers to distributions *after* W mass cut 
    - fail refers to distributions failing Hbb tag score (after stage2) 
    - pass refers to distributions passing Hbb tag score (after stage2)

to-do: figure out H mass cut? CR?

'''

from collections import OrderedDict
import ROOT
from TIMBER.Tools.Common import CompileCpp
from TIMBER.Analyzer import HistGroup
from argparse import ArgumentParser
from XHYbbWW_class import XHYbbWW
ROOT.gROOT.SetBatch(True)

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

CompileCpp('HWWmodules.cc')
CompileCpp('GenMatchFunctions.cc')

controlPlots = []

filename = f'trijet_nano/{args.setname}_{args.era}_snapshot.txt'
selection = XHYbbWW(filename, args.era, 1, 1)
checkpoint = selection.OpenForSelection(args.variation, runCorrs=True) # generate corrections, even if they are not used here

if ('NMSSM' not in args.setname):
    raise ValueError(f'This script is for signal only, will not run on {args.signame}...')

checkpoint = selection.a.Define('Trijet_GenMatchCats','classifyProbeJets({0,1,2}, Trijet_phi, Trijet_eta, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother)')
for i in range(3):
    selection.a.Define(f'JET{i}_genmatch',f'Trijet_GenMatchCats[{i}]')
    selection.a.DataFrame.Display([f'JET{i}_genmatch']).Print()

checkpoint = selection.a.MakeWeightCols(
    correctionNames = list(selection.a.GetCorrectionNames()),
    extraNominal = '' if selection.a.isData else f'{selection.GetXsecScale()}'
)
weight_col = 'weight__nominal'

# 0:top, 1:W, 2:H, 3:other, 4:multiple
statuses = OrderedDict([(0,'top-bqq'), (1,'W'), (2,'H'), (3,'other'), (4,'multiple')])
controlPlots = []

#########################################################################
#        STAGE 1 : control plots before any tagger cuts                 #
#########################################################################
for iJet in range(3):
    for property in ['particleNet_mass','msoftdrop_corr','pt_corr','particleNetMD_WvsQCD','particleNetMD_HbbvsQCD']:
        print(f'pre-tagger-cuts : {property} Jet {iJet}')
        selection.a.Define(f'Jet{iJet}_{property}',f'Trijet_{property}[{iJet}]')
        if 'particleNet_mass' in property:
            model = (f"preselection_{property}_{iJet}",f"{property} Jet {iJet}",60,0,300)
        elif 'pt' in property:
            model = (f"preselection_{property}_{iJet}",f"{property} Jet {iJet}",100,200,2200)
        elif 'particleNet' in property:
            model = (f"preselection_{property}_{iJet}",f"{property} Jet {iJet}",50,0,1)
        print(model)
        hTemp = selection.a.DataFrame.Histo1D(model,f'Jet{iJet}_{property}',weight_col)
        hTemp.SetDirectory(0)
        controlPlots.append(hTemp)

#########################################################################
#        STAGE 2 : control plots before any tagger cuts                 #
#########################################################################
# MD_WvsQCD working points. Per year, given by Loose(2.5%), Medium(1%), Tight(0.5%)
# https://twiki.cern.ch/twiki/bin/view/CMS/ParticleNetSFs
wps = {
    '16APV': [0.637, 0.845, 0.910],
    '16': [0.642, 0.842, 0.907],
    '17': [0.579, 0.810, 0.891],
    '18': [0.59, 0.82, 0.90]
}
for i, wp in enumerate(wps[args.era]):
    if i > 0: continue  # we are sticking with the loose 2.5% WP
    selection.a.SetActiveNode(checkpoint)
    print('-----------------------------------------------------------------------')
    print(f'SIGNAL REGION USING WvsQCD WP {wp}')
    print('-----------------------------------------------------------------------')


    print('Step 1: assign Higgs candidate')
    selection.a.Define(f'Higgs_candidate_idx_SR{i}','Pick_H_candidate(Trijet_particleNetMD_HbbvsQCD,{0,1,2})')
    #selection.a.DataFrame.Display([f'Higgs_candidate_idx_SR{i}']).Print()
    # have to make dummy columns otherwise RDF complains...
    selection.a.Define(f'DummyW_idx0_SR{i}',f'Higgs_candidate_idx_SR{i}[1]') # the 0th index belongs to Higgs candidate 
    selection.a.Define(f'DummyW_idx1_SR{i}',f'Higgs_candidate_idx_SR{i}[2]') # the 0th index belongs to Higgs candidate
    #selection.a.DataFrame.Display([f'DummyW_idx0_SR{i}']).Print()
    #selection.a.DataFrame.Display([f'DummyW_idx1_SR{i}']).Print()


    print('Step 2: assign W candidates')
    selection.a.Define(f'W_candidate_idxs_SR{i}','Pick_W_candidates(Trijet_particleNetMD_WvsQCD, %s, {DummyW_idx0_SR%s, DummyW_idx1_SR%s})'%(wp,i,i))
    #selection.a.DataFrame.Display([f'W_candidate_idxs_SR{i}']).Print()

    print('Step 3: create H/W1/W2 collections')
    selection.a.Define(f'H_idx_SR{i}',f'Higgs_candidate_idx_SR{i}[0]')
    selection.a.Define(f'W1_idx_SR{i}',f'W_candidate_idxs_SR{i}[0]')
    selection.a.Define(f'W2_idx_SR{i}',f'W_candidate_idxs_SR{i}[1]')
    selection.a.Cut(f'Has2Ws_SR{i}',f'(W1_idx_SR{i} >= 0) && (W2_idx_SR{i} >= 0)')


    cols_to_skip = ['vect_msoftdrop','vect_particleNet_mass','vect_msoftdrop_corr','vect_particleNet_mass','tau2','tau3','tau1','tau4','particleNetMD_QCD','deepTagMD_HbbvsQCD','particleNet_TvsQCD','particleNetMD_Xcc','deepTagMD_WvsQCD','particleNet_QCD','jetId','particleNetMD_Xbb','particleNet_WvsQCD','deepTagMD_ZHbbvsQCD','deepTag_TvsQCD','rawFactor','particleNetMD_Xqq']
    cols = ['Trijet_%s'%i for i in cols_to_skip]
    selection.a.ObjectFromCollection(f'H_SR{i}','Trijet',f'H_idx_SR{i}',skip=cols)
    selection.a.ObjectFromCollection(f'W1_SR{i}','Trijet',f'W1_idx_SR{i}',skip=cols)
    selection.a.ObjectFromCollection(f'W2_SR{i}','Trijet',f'W2_idx_SR{i}',skip=cols)

    print('Step 4: Make TLvectors, calculate invariant masses')
    selection.a.Define(f'Higgs_vect_SR{i}',f'hardware::TLvector(H_SR{i}_pt_corr,H_SR{i}_eta,H_SR{i}_phi,H_SR{i}_msoftdrop_corr)')
    selection.a.Define(f'LeadW_vect_SR{i}',f'hardware::TLvector(W1_SR{i}_pt_corr,W1_SR{i}_eta,W1_SR{i}_phi,W1_SR{i}_msoftdrop_corr)')
    selection.a.Define(f'SubleadW_vect_SR{i}',f'hardware::TLvector(W1_SR{i}_pt_corr,W2_SR{i}_eta,W2_SR{i}_phi,W2_SR{i}_msoftdrop_corr)')

    selection.a.Define(f'mhww_SR{i}','hardware::InvariantMass({LeadW_vect_SR%s, SubleadW_vect_SR%s, Higgs_vect_SR%s})'%(i,i,i))
    selection.a.Define(f'mww_SR{i}','hardware::InvariantMass({LeadW_vect_SR%s, SubleadW_vect_SR%s})'%(i,i))

    # Get the index of the gen-matched particles for each candidate
    for jet in [f'H_SR{i}',f'W1_SR{i}',f'W2_SR{i}']:
        selection.a.Define(f'{jet}_genMatchIdx',f'get_genpart_idx({jet}_GenMatchCats, {jet}_phi, {jet}_eta, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother)')
        selection.a.Define(f'{jet}_matched_pt',f'GenPart_pt[{jet}_genMatchIdx]')
        selection.a.Define(f'{jet}_matched_mass',f'GenPart_mass[{jet}_genMatchIdx]')

    print('Step 5: Make some control plots')
    for particle in [f'H_SR{i}',f'W1_SR{i}',f'W2_SR{i}']:
        for var in ['particleNetMD_WvsQCD', 'particleNetMD_HbbvsQCD', 'pt_corr', 'msoftdrop_corr', 'particleNet_mass', 'matched_pt', 'matched_mass', 'GenMatchCats']:
            if 'vsQCD' in var:
                model = (f'SR{i}_stage1_{particle}_{var}',f'SR{i} stage 1 {particle} {var}',50,0,1)
            elif 'pt' in var:
                model = (f'SR{i}_stage1_{particle}_{var}',f'SR{i} stage 1 {particle} {var}',100,200,1200)
            elif ('particleNet_mass' in var) or ('softdrop' in var):
                model = (f'SR{i}_stage1_{particle}_{var}',f'SR{i} stage 1 {particle} {var}',60,0,300)
            elif 'matched_mass' in var:
                model = (f'SR{i}_stage1_{particle}_{var}',f'',60,0,300)

            print(f'Making plot of {model[1]}')
            hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}',weight_col)
            hTemp.SetDirectory(0)
            controlPlots.append(hTemp)
    for mxmy in [f'mhww_SR{i}',f'mww_SR{i}']:
        mass = mxmy.split('_')[0]
        model = (f'SR{i}_stage1_{mass}',f'',100,0,3000)
        hTemp = selection.a.DataFrame.Histo1D(model,mxmy,weight_col)
        hTemp.SetDirectory(0)
        controlPlots.append(hTemp)

'''
    print('Step 6: Apply W mass cut')
    mW1 = f'W1_SR{i}_particleNet_mass'
    mW2 = f'W2_SR{i}_particleNet_mass'
    window = [60., 110.]
    mW_cut = f'({mW1} >= {window[0]}) && ({mW1} <= {window[1]}) && ({mW2} >= {window[0]}) && ({mW2} <= {window[1]})'
    PF_CHECKPOINT = selection.a.Cut(f'mW_window_cut_SR{i}',mW_cut)

    cuts[f'SR{i}_n_after_WmassCut'] = selection.getNweighted()

    print('Step 7: Make some more control plots after W mass cut')
    for particle in [f'H_SR{i}',f'W1_SR{i}',f'W2_SR{i}']:
        for var in ['particleNetMD_WvsQCD', 'particleNetMD_HbbvsQCD', 'pt_corr', 'particleNet_mass']:
            if 'vsQCD' in var:
                model = (f'SR{i}_stage2_{particle}_{var}',f'SR{i} stage 2 {particle} {var}',50,0,1)
            elif 'pt' in var:
                model = (f'SR{i}_stage2_{particle}_{var}',f'SR{i} stage 2 {particle} {var}',100,200,1200)
            elif 'particleNet_mass' in var:
                model = (f'SR{i}_stage2_{particle}_{var}',f'SR{i} stage 2 {particle} {var}',60,0,300)

            print(f'Making plot of {model[1]}')
            if isData:
                hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}')
            else:   
                hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}',weight_col)
            hTemp.SetDirectory(0)
            controlPlots.append(hTemp)
    for mxmy in [f'mhww_SR{i}',f'mww_SR{i}']:
        mass = mxmy.split('_')[0]
        model = (f'SR{i}_stage2_{mass}',f'',100,0,3000)
        if isData:
            hTemp = selection.a.DataFrame.Histo1D(model,mxmy)
        else:   
            hTemp = selection.a.DataFrame.Histo1D(model,mxmy,weight_col)
        hTemp.SetDirectory(0)
        controlPlots.append(hTemp)

    print('Step 8: create Pass/Fail distributions using Hbb score')
    for pf in ['pass','fail']:
        for lowerBound in ['0.0','0.2']:
            selection.a.SetActiveNode(PF_CHECKPOINT)
            print('----------------------------------------------')
            print(f'Creating SR {pf} with lower bound (fail) {lowerBound}')
            print('----------------------------------------------')
            cutName = f'SR{i}_Hbb_{pf}{lowerBound.replace(".","p")}_cut'
            if pf == 'pass':
                cutVal = f'H_SR{i}_particleNetMD_HbbvsQCD >= 0.98'
            else:
                cutVal = f'(H_SR{i}_particleNetMD_HbbvsQCD >= {lowerBound}) && (H_SR{i}_particleNetMD_HbbvsQCD < 0.98)'
            selection.a.Cut(cutName,cutVal)

            lowerBound = lowerBound.replace(".","p")
            cuts[f'SR{i}_{pf}{lowerBound}'] = selection.getNweighted()

            # now make control plots 
            for particle in [f'H_SR{i}',f'W1_SR{i}',f'W2_SR{i}']:
                for var in ['particleNetMD_WvsQCD', 'particleNetMD_HbbvsQCD', 'pt_corr', 'particleNet_mass']:
                    if 'vsQCD' in var:
                        model = (f'SR{i}_{pf}{lowerBound}_{particle}_{var}',f'SR{i} {pf} {lowerBound} {particle} {var}',50,0,1)
                    elif 'pt' in var:
                        model = (f'SR{i}_{pf}{lowerBound}_{particle}_{var}',f'SR{i} {pf} {lowerBound} {particle} {var}',100,200,1200)
                    elif 'particleNet_mass' in var:
                        model = (f'SR{i}_{pf}{lowerBound}_{particle}_{var}',f'SR{i} {pf} {lowerBound} {particle} {var}',60,0,300)

                    print(f'Making plot of {model[1]}')
                    if isData:
                        hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}')
                    else:   
                        hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}',weight_col)
                    hTemp.SetDirectory(0)
                    controlPlots.append(hTemp)
            for mxmy in [f'mhww_SR{i}',f'mww_SR{i}']:
                mass = mxmy.split('_')[0]
                model = (f'SR{i}_{pf}{lowerBound}_{mass}',f'',100,0,3000)
                if isData:
                    hTemp = selection.a.DataFrame.Histo1D(model,mxmy)
                else:   
                    hTemp = selection.a.DataFrame.Histo1D(model,mxmy,weight_col)
                hTemp.SetDirectory(0)
                controlPlots.append(hTemp)

            # Now apply the Higgs mass cut 
            if pf == 'pass':
                print(f'-----------------------------------------------------------------')
                print(f'Creating pass with Hbb mass window cut')
                print(f'-----------------------------------------------------------------')
                cutval = f'(H_SR{i}_particleNet_mass >= 100) && (H_SR{i}_particleNet_mass <= 150)'
                cutname = f'SR{i}_Hbb_{pf}{lowerBound.replace(".","p")}_mass_cut'
                selection.a.Cut(cutname,cutval)
                cuts[f'SR{i}_{pf}{lowerBound}_HbbMass'] = selection.getNweighted()

                # make control plots
                for particle in [f'H_SR{i}',f'W1_SR{i}',f'W2_SR{i}']:
                    for var in ['particleNetMD_WvsQCD', 'particleNetMD_HbbvsQCD', 'pt_corr', 'particleNet_mass']:
                        if 'vsQCD' in var:
                            model = (f'SR{i}_{pf}{lowerBound}_HbbMassCut_{particle}_{var}',f'SR{i} {pf} {lowerBound} Hbb mass cut {particle} {var}',50,0,1)
                        elif 'pt' in var:
                            model = (f'SR{i}_{pf}{lowerBound}_HbbMassCut_{particle}_{var}',f'SR{i} {pf} {lowerBound} Hbb mass cut {particle} {var}',100,200,1200)
                        elif 'particleNet_mass' in var:
                            model = (f'SR{i}_{pf}{lowerBound}_HbbMassCut_{particle}_{var}',f'SR{i} {pf} {lowerBound} Hbb mass cut {particle} {var}',60,0,300)

                        print(f'Making plot of {model[1]}')
                        if isData:
                            hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}')
                        else:
                            hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}',weight_col)
                        hTemp.SetDirectory(0)
                        controlPlots.append(hTemp)

                for mxmy in [f'mhww_SR{i}',f'mww_SR{i}']:
                    mass = mxmy.split('_')[0]
                    model = (f'SR{i}_{pf}{lowerBound}_HbbMassCut_{mass}',f'',100,0,3000)
                    if isData:
                        hTemp = selection.a.DataFrame.Histo1D(model,mxmy)
                    else:
                        hTemp = selection.a.DataFrame.Histo1D(model,mxmy,weight_col)
                    hTemp.SetDirectory(0)
                    controlPlots.append(hTemp)

                # plot gen matching for tops only
                if ('ttbar' in args.setname):
                    for jet in ['H','W1','W2']: # W1_SR0_GenMatchCats
                        # plot the generator ID for each jet 
                        hGenStatus = selection.a.GetActiveNode().DataFrame.Histo1D(
                            (f'SR{i}_{jet}_{pf}{lowerBound}_HbbMassCut_GenMatchStatus', f'SR{i} {jet} {pf} {lowerBound} Hbb mass cut gen match status', len(statuses), 0.5, len(statuses)+0.5),
                            f'{jet}_SR{i}_GenMatchCats','weight__nominal'
                        )
                        hGenStatus.SetDirectory(0)
                        controlPlots.append(hGenStatus)
'''

fOut = ROOT.TFile.Open(f'rootfiles/GenMatchSignalStudies_{args.setname}_{args.era}.root','RECREATE')
fOut.cd()
for plot in controlPlots:
    print(f'Writing {plot.GetName()} to file....')
    plot.Write()

fOut.Close()
