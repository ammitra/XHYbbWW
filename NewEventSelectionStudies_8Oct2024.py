'''
Script for testing new event selection strategy for XHY 

1. preselection
2. identify Higgs candidate as jet with leading Higgs score 
3. Perform assignment of W candidates 
    - SR = both Ws pass PNetMD_WvsQCD 2.5% mistag WP
4. Perform Higgs pass/fail cut 
    - try different lower bounds for Fail 


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

controlPlots = []

filename = f'trijet_nano/{args.setname}_{args.era}_snapshot.txt'
selection = XHYbbWW(filename, args.era, 1, 1)
checkpoint = selection.OpenForSelection(args.variation)

# store cutflow 
cuts = OrderedDict()

cuts['Pretag'] = selection.getNweighted()

# weight if MC, don't weight if data
isData = True if 'Data' in args.setname else False
weight_col = 'weight__nominal'

#########################################################################
#        STAGE 1 : control plots before any tagger cuts                 #
#########################################################################
for iJet in range(3):
    for property in ['mregressed_corr','pt_corr','particleNetMD_WvsQCD','particleNetMD_HbbvsQCD']:
        print(f'pre-tagger-cuts : {property} Jet {iJet}')
        selection.a.Define(f'Jet{iJet}_{property}',f'Trijet_{property}[{iJet}]')
        if 'mregressed' in property:
            model = (f"STAGE1_{property}_{iJet}",f"{property} Jet {iJet}",60,0,300)
        elif 'pt' in property:
            model = (f"STAGE1_{property}_{iJet}",f"{property} Jet {iJet}",100,200,2200)
        elif 'particleNet' in property:
            model = (f"STAGE1_{property}_{iJet}",f"{property} Jet {iJet}",50,0,1)
        if isData:
            hTemp = selection.a.DataFrame.Histo1D(model,f'Jet{iJet}_{property}')
        else:
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

    cuts[f'SR{i}_n_after_Has2Ws'] = selection.getNweighted()

    cols_to_skip = ['vect_msoftdrop','vect_mregressed','vect_msoftdrop_corr','vect_mregressed_corr','tau2','tau3','tau1','tau4','particleNetMD_QCD','deepTagMD_HbbvsQCD','particleNet_TvsQCD','particleNetMD_Xcc','deepTagMD_WvsQCD','particleNet_QCD','jetId','particleNetMD_Xbb','particleNet_WvsQCD','deepTagMD_ZHbbvsQCD','deepTag_TvsQCD','rawFactor','particleNetMD_Xqq']
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

    print('Step 5: Make some control plots')
    for particle in [f'H_SR{i}',f'W1_SR{i}',f'W2_SR{i}']:
        for var in ['particleNetMD_WvsQCD', 'particleNetMD_HbbvsQCD', 'pt_corr', 'mregressed_corr']:
            if 'particle' in var:
                model = (f'SR{i}_stage1_{particle}_{var}',f'SR{i} stage 1 {particle} {var}',50,0,1)
            elif 'pt' in var:
                model = (f'SR{i}_stage1_{particle}_{var}',f'SR{i} stage 1 {particle} {var}',100,200,1200)
            elif 'regressed' in var:
                model = (f'SR{i}_stage1_{particle}_{var}',f'SR{i} stage 1 {particle} {var}',60,0,300)

            print(f'Making plot of {model[1]}')
            if isData:
                hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}')
            else:   
                hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}',weight_col)
            hTemp.SetDirectory(0)
            controlPlots.append(hTemp)
    for mxmy in [f'mhww_SR{i}',f'mww_SR{i}']:
        mass = mxmy.split('_')[0]
        model = (f'SR{i}_stage1_{mass}',f'',100,0,3000)
        if isData:
            hTemp = selection.a.DataFrame.Histo1D(model,mxmy)
        else:   
            hTemp = selection.a.DataFrame.Histo1D(model,mxmy,weight_col)
        hTemp.SetDirectory(0)
        controlPlots.append(hTemp)


    print('Step 6: Apply W mass cut')
    mW1 = f'W1_SR{i}_mregressed_corr'
    mW2 = f'W2_SR{i}_mregressed_corr'
    window = [60., 110.]
    mW_cut = f'({mW1} >= {window[0]}) && ({mW1} <= {window[1]}) && ({mW2} >= {window[0]}) && ({mW2} <= {window[1]})'
    PF_CHECKPOINT = selection.a.Cut(f'mW_window_cut_SR{i}',mW_cut)

    cuts[f'SR{i}_n_after_WmassCut'] = selection.getNweighted()

    print('Step 7: Make some more control plots after W mass cut')
    for particle in [f'H_SR{i}',f'W1_SR{i}',f'W2_SR{i}']:
        for var in ['particleNetMD_WvsQCD', 'particleNetMD_HbbvsQCD', 'pt_corr', 'mregressed_corr']:
            if 'particle' in var:
                model = (f'SR{i}_stage2_{particle}_{var}',f'SR{i} stage 2 {particle} {var}',50,0,1)
            elif 'pt' in var:
                model = (f'SR{i}_stage2_{particle}_{var}',f'SR{i} stage 2 {particle} {var}',100,200,1200)
            elif 'regressed' in var:
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
                for var in ['particleNetMD_WvsQCD', 'particleNetMD_HbbvsQCD', 'pt_corr', 'mregressed_corr']:
                    if 'particle' in var:
                        model = (f'SR{i}_{pf}{lowerBound}_{particle}_{var}',f'SR{i} {pf} {lowerBound} {particle} {var}',50,0,1)
                    elif 'pt' in var:
                        model = (f'SR{i}_{pf}{lowerBound}_{particle}_{var}',f'SR{i} {pf} {lowerBound} {particle} {var}',100,200,1200)
                    elif 'regressed' in var:
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




fOut = ROOT.TFile.Open(f'rootfiles/NewSelectionStudies_{args.setname}_{args.era}.root','RECREATE')
fOut.cd()
for plot in controlPlots:
    print('Writing {plot.GetTitle()} to file....')
    plot.Write()

# Save out cutflow information
hCutflow = ROOT.TH1F('cutflow','Number of events after each cut',len(cuts),0.5,len(cuts)+0.5)
nBin = 1
for cutname, cutval in cuts.items():
    print(f'Obtaining cutflow for {cutname}')
    nCut = cutval.GetValue()
    print(f'{cutname} = {nCut}')
    hCutflow.GetXaxis().SetBinLabel(nBin,cutname)
    hCutflow.AddBinContent(nBin,nCut)
    nBin += 1
print('Writing cutflow histogram to file')
hCutflow.Write()

fOut.Close()
