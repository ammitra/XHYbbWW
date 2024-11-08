'''
Script for testing new event selection strategy for XHY 

1. preselection
    - add additional mSD > 50 cut
2. identify Higgs candidate as jet with leading Higgs score 

----------------SR----------------
* [100, 150] mH
* [60, 110] mW
* pass: Hbb>=0.98
* fail: 0<Hbb<0.98

----------------VR----------------
* same as SR, but in the Hbb sidebands
* (75<=mH<100) or (100<mH<=175)

Histogram naming keys:
    - WP0,1,2 correspond to selections using loose,medium,tight MD_WvsQCD WP
    - preselection refers to pre-tag distributions
    - stage1 refers to distributions *before* W mass cut 
    - stage2 refers to distributions *after* W mass cut 
    - fail refers to distributions failing Hbb tag score (after stage2) 
    - pass refers to distributions passing Hbb tag score (after stage2)


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

controlPlots = []

filename = f'trijet_nano/{args.setname}_{args.era}_snapshot.txt'
selection = XHYbbWW(filename, args.era, 1, 1)
checkpoint = selection.OpenForSelection(args.variation, runCorrs=True) # generate corrections, even if they are not used here

# store cutflow 
cuts = OrderedDict()

cuts['Pretag'] = selection.getNweighted()

checkpoint = selection.a.MakeWeightCols(
    correctionNames = list(selection.a.GetCorrectionNames()),
    extraNominal = '' if selection.a.isData else f'{selection.GetXsecScale()}'
)

# weight if MC, don't weight if data
isData = True if 'Data' in args.setname else False
weight_col = 'weight__nominal'

'''
checkpoint = selection.a.Cut('msd_cut','Trijet_msoftdrop[0] > 50 && Trijet_msoftdrop[1] > 50 && Trijet_msoftdrop[2] > 50')

cuts['msoftdrop_cut'] = selection.getNweighted()
'''

#########################################################################
#        STAGE 1 : control plots before any tagger cuts                 #
#########################################################################
for iJet in range(3):
    for var in ['particleNet_mass','msoftdrop','msoftdrop_corr','pt','pt_corr','particleNetMD_WvsQCD','particleNetMD_HbbvsQCD']:
        print(f'pre-tagger-cuts : {var} Jet {iJet}')
        selection.a.Define(f'Jet{iJet}_{var}',f'Trijet_{var}[{iJet}]')
        if ('particleNet_mass' in var) or ('softdrop' in var):
            model = (f"preselection_{var}_{iJet}",f"",60,0,300)
        elif 'pt' in var:
            model = (f"preselection_{var}_{iJet}",f"",100,200,2200)
        elif 'particleNet' in var:
            model = (f"preselection_{var}_{iJet}",f"",50,0,1)
        if isData:
            hTemp = selection.a.DataFrame.Histo1D(model,f'Jet{iJet}_{var}')
        else:
            hTemp = selection.a.DataFrame.Histo1D(model,f'Jet{iJet}_{var}',weight_col)
        hTemp.SetDirectory(0)
        controlPlots.append(hTemp)

#########################################################################
#        STAGE 2 : start applying tagger and mass cuts                  #
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
    selection.a.Define(f'Higgs_candidate_idx_WP{i}','Pick_H_candidate(Trijet_particleNetMD_HbbvsQCD,{0,1,2})')
    #selection.a.DataFrame.Display([f'Higgs_candidate_idx_WP{i}']).Print()
    # have to make dummy columns otherwise RDF complains...
    selection.a.Define(f'DummyW_idx0_WP{i}',f'Higgs_candidate_idx_WP{i}[1]') # the 0th index belongs to Higgs candidate 
    selection.a.Define(f'DummyW_idx1_WP{i}',f'Higgs_candidate_idx_WP{i}[2]') # the 0th index belongs to Higgs candidate
    #selection.a.DataFrame.Display([f'DummyW_idx0_WP{i}']).Print()
    #selection.a.DataFrame.Display([f'DummyW_idx1_WP{i}']).Print()


    print('Step 2: assign W candidates')
    selection.a.Define(f'W_candidate_idxs_WP{i}','Pick_W_candidates(Trijet_particleNetMD_WvsQCD, %s, {DummyW_idx0_WP%s, DummyW_idx1_WP%s})'%(wp,i,i))
    #selection.a.DataFrame.Display([f'W_candidate_idxs_WP{i}']).Print()

    print('Step 3: create H/W1/W2 collections')
    selection.a.Define(f'H_idx_WP{i}',f'Higgs_candidate_idx_WP{i}[0]')
    selection.a.Define(f'W1_idx_WP{i}',f'W_candidate_idxs_WP{i}[0]')
    selection.a.Define(f'W2_idx_WP{i}',f'W_candidate_idxs_WP{i}[1]')
    selection.a.Cut(f'Has2Ws_WP{i}',f'(W1_idx_WP{i} >= 0) && (W2_idx_WP{i} >= 0)')

    cuts[f'WP{i}_n_after_Has2Ws'] = selection.getNweighted()

    cols_to_skip = ['vect_msoftdrop','vect_particleNet_mass','vect_msoftdrop_corr','vect_particleNet_mass','tau2','tau3','tau1','tau4','particleNetMD_QCD','deepTagMD_HbbvsQCD','particleNet_TvsQCD','particleNetMD_Xcc','deepTagMD_WvsQCD','particleNet_QCD','jetId','particleNetMD_Xbb','particleNet_WvsQCD','deepTagMD_ZHbbvsQCD','deepTag_TvsQCD','rawFactor','particleNetMD_Xqq']
    cols = ['Trijet_%s'%i for i in cols_to_skip]
    selection.a.ObjectFromCollection(f'H_WP{i}','Trijet',f'H_idx_WP{i}',skip=cols)
    selection.a.ObjectFromCollection(f'W1_WP{i}','Trijet',f'W1_idx_WP{i}',skip=cols)
    selection.a.ObjectFromCollection(f'W2_WP{i}','Trijet',f'W2_idx_WP{i}',skip=cols)

    print('Step 4: Make TLvectors, calculate invariant masses')
    # First do it with the corrected pt
    selection.a.Define(f'Higgs_vect_WP{i}',f'hardware::TLvector(H_WP{i}_pt_corr,H_WP{i}_eta,H_WP{i}_phi,H_WP{i}_msoftdrop_corr)')
    selection.a.Define(f'LeadW_vect_WP{i}',f'hardware::TLvector(W1_WP{i}_pt_corr,W1_WP{i}_eta,W1_WP{i}_phi,W1_WP{i}_msoftdrop_corr)')
    selection.a.Define(f'SubleadW_vect_WP{i}',f'hardware::TLvector(W2_WP{i}_pt_corr,W2_WP{i}_eta,W2_WP{i}_phi,W2_WP{i}_msoftdrop_corr)')
    selection.a.Define(f'mhww_WP{i}','hardware::InvariantMass({LeadW_vect_WP%s, SubleadW_vect_WP%s, Higgs_vect_WP%s})'%(i,i,i))
    selection.a.Define(f'mww_WP{i}','hardware::InvariantMass({LeadW_vect_WP%s, SubleadW_vect_WP%s})'%(i,i))
    # Now do it with the uncorrected pt just to check
    selection.a.Define(f'Higgs_vect_WP{i}_nocorr',f'hardware::TLvector(H_WP{i}_pt,H_WP{i}_eta,H_WP{i}_phi,H_WP{i}_msoftdrop_corr)')
    selection.a.Define(f'LeadW_vect_WP{i}_nocorr',f'hardware::TLvector(W1_WP{i}_pt,W1_WP{i}_eta,W1_WP{i}_phi,W1_WP{i}_msoftdrop_corr)')
    selection.a.Define(f'SubleadW_vect_WP{i}_nocorr',f'hardware::TLvector(W2_WP{i}_pt,W2_WP{i}_eta,W2_WP{i}_phi,W2_WP{i}_msoftdrop_corr)')
    selection.a.Define(f'mhww_WP{i}_nocorr','hardware::InvariantMass({LeadW_vect_WP%s_nocorr, SubleadW_vect_WP%s_nocorr, Higgs_vect_WP%s_nocorr})'%(i,i,i))
    selection.a.Define(f'mww_WP{i}_nocorr','hardware::InvariantMass({LeadW_vect_WP%s_nocorr, SubleadW_vect_WP%s_nocorr})'%(i,i))

    print('Step 5: Make some control plots')
    for particle in [f'H_WP{i}',f'W1_WP{i}',f'W2_WP{i}']:
        for var in ['particleNetMD_WvsQCD', 'particleNetMD_HbbvsQCD', 'pt', 'pt_corr', 'msoftdrop', 'msoftdrop_corr', 'particleNet_mass']:
            if 'vsQCD' in var:
                model = (f'WP{i}_stage1_{particle}_{var}','',50,0,1)
            elif 'pt' in var:
                model = (f'WP{i}_stage1_{particle}_{var}','',100,200,1200)
            elif ('particleNet_mass' in var) or ('softdrop' in var):
                model = (f'WP{i}_stage1_{particle}_{var}','',60,0,300)

            print(f'Making plot of {model[0]}')
            if isData:
                hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}')
            else:   
                hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}',weight_col)
            hTemp.SetDirectory(0)
            controlPlots.append(hTemp)
    for mxmy in [f'mhww_WP{i}',f'mww_WP{i}',f'mhww_WP{i}_nocorr',f'mww_WP{i}_nocorr']:
        mass = mxmy.split('_')[0] + ('_nocorr' if '_nocorr' in mxmy else '')
        model = (f'WP{i}_stage1_{mass}','',100,0,3000)
        print(f'Making plot of {model[0]}')
        if isData:
            hTemp = selection.a.DataFrame.Histo1D(model,mxmy)
        else:   
            hTemp = selection.a.DataFrame.Histo1D(model,mxmy,weight_col)
        hTemp.SetDirectory(0)
        controlPlots.append(hTemp)


    print('Step 6: Apply W mass cut')
    mW1 = f'W1_WP{i}_particleNet_mass'
    mW2 = f'W2_WP{i}_particleNet_mass'
    window = [60., 110.]
    mW_cut = f'({mW1} >= {window[0]}) && ({mW1} <= {window[1]}) && ({mW2} >= {window[0]}) && ({mW2} <= {window[1]})'
    PF_CHECKPOINT = selection.a.Cut(f'mW_window_cut_WP{i}',mW_cut)

    cuts[f'WP{i}_n_after_WmassCut'] = selection.getNweighted()

    print('Step 7: Make some more control plots after W mass cut')
    for particle in [f'H_WP{i}',f'W1_WP{i}',f'W2_WP{i}']:
        for var in ['particleNetMD_WvsQCD', 'particleNetMD_HbbvsQCD', 'pt', 'pt_corr', 'msoftdrop', 'msoftdrop_corr', 'particleNet_mass']:
            if 'vsQCD' in var:
                model = (f'WP{i}_stage2_{particle}_{var}',f'WP{i} stage 2 {particle} {var}',50,0,1)
            elif 'pt' in var:
                model = (f'WP{i}_stage2_{particle}_{var}',f'WP{i} stage 2 {particle} {var}',100,200,1200)
            elif ('particleNet_mass' in var) or ('softdrop' in var):
                model = (f'WP{i}_stage2_{particle}_{var}',f'WP{i} stage 2 {particle} {var}',60,0,300)

            print(f'Making plot of {model[0]}')
            if isData:
                hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}')
            else:   
                hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}',weight_col)
            hTemp.SetDirectory(0)
            controlPlots.append(hTemp)
    for mxmy in [f'mhww_WP{i}',f'mww_WP{i}',f'mhww_WP{i}_nocorr',f'mww_WP{i}_nocorr']:
        mass = mxmy.split('_')[0] + ('_nocorr' if '_nocorr' in mxmy else '')
        model = (f'WP{i}_stage2_{mass}','',100,0,3000)
        print(f'Making plot of {model[0]}')
        if isData:
            hTemp = selection.a.DataFrame.Histo1D(model,mxmy)
        else:   
            hTemp = selection.a.DataFrame.Histo1D(model,mxmy,weight_col)
        hTemp.SetDirectory(0)
        controlPlots.append(hTemp)


    print('Step 8: create SR and VR')
    for region in ['SR', 'VR']:
        selection.a.SetActiveNode(PF_CHECKPOINT)
        print(f'-----------------------------------------------------------------')
        print(f'Creating {region} with corresponding mass window requirement')
        print(f'-----------------------------------------------------------------')
        if region == 'SR':
            # Higgs mass window
            cutval = f'(H_WP{i}_particleNet_mass >= 100) && (H_WP{i}_particleNet_mass <= 150)'
        else: 
            # Higgs mass sidebands
            cutval = f'((H_WP{i}_particleNet_mass >= 75) && (H_WP{i}_particleNet_mass <= 100)) || ((H_WP{i}_particleNet_mass > 150) && (H_WP{i}_particleNet_mass <= 175))'
        cutname = f'WP{i}_{region}_Hbb_mass_cut'
        SR_CR_checkpoint = selection.a.Cut(cutname,cutval)
        cuts[f'WP{i}_{region}_HbbMassCut'] = selection.getNweighted()

        # now make control plots 
        for particle in [f'H_WP{i}',f'W1_WP{i}',f'W2_WP{i}']:
            for var in ['particleNetMD_WvsQCD', 'particleNetMD_HbbvsQCD', 'pt', 'pt_corr', 'msoftdrop', 'msoftdrop_corr', 'particleNet_mass']:
                if 'vsQCD' in var:
                    model = (f'WP{i}_{region}_HbbMass_{particle}_{var}','',50,0,1)
                elif 'pt' in var:
                    model = (f'WP{i}_{region}_HbbMass_{particle}_{var}','',100,200,1200)
                elif ('particleNet_mass' in var) or ('softdrop' in var):
                    model = (f'WP{i}_{region}_HbbMass_{particle}_{var}','',60,0,300)

                print(f'Making plot of {model[0]}')
                if isData:
                    hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}')
                else:
                    hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}',weight_col)
                hTemp.SetDirectory(0)
                controlPlots.append(hTemp)
        for mxmy in [f'mhww_WP{i}',f'mww_WP{i}',f'mhww_WP{i}_nocorr',f'mww_WP{i}_nocorr']:
            mass = mxmy.split('_')[0] + ('_nocorr' if '_nocorr' in mxmy else '')
            model = (f'WP{i}_{region}_HbbMass_{mass}','',100,0,3000)
            print(f'Making plot of {model[0]}')
            if isData:
                hTemp = selection.a.DataFrame.Histo1D(model,mxmy)
            else:
                hTemp = selection.a.DataFrame.Histo1D(model,mxmy,weight_col)
            hTemp.SetDirectory(0)
            controlPlots.append(hTemp)

        # Now create Pass and Fail based on Hbb score cut
        for pf in ['fail_0.0','fail_0.2','pass']:
            selection.a.SetActiveNode(SR_CR_checkpoint) # reset to the checkpoint before making pass/fail so they start from the same events
            if 'fail' in pf:
                lowerBound = pf.split('_')[-1]
                cutVal  = f'(H_WP{i}_particleNetMD_HbbvsQCD > {lowerBound}) && (H_WP{i}_particleNetMD_HbbvsQCD < 0.98)'
                cutname = f'WP{i}_{region}_{pf.replace(".","p")}_HbbCut'
            else:
                cutVal  = f'H_WP{i}_particleNetMD_HbbvsQCD >= 0.98'
                cutname = f'WP{i}_{region}_{pf}_HbbCut'

            pf = pf.replace('.','p') if 'fail' in pf else pf
            selection.a.Cut(cutname,cutVal)
            cuts[f'WP{i}_{region}_{pf}_HbbScoreCut'] = selection.getNweighted()

            # Now make control plots
            for particle in [f'H_WP{i}',f'W1_WP{i}',f'W2_WP{i}']:
                for var in ['particleNetMD_WvsQCD', 'particleNetMD_HbbvsQCD', 'pt', 'pt_corr', 'msoftdrop', 'msoftdrop_corr', 'particleNet_mass']:
                    if 'vsQCD' in var:
                        model = (f'WP{i}_{region}_{pf}_{particle}_{var}','',50,0,1)
                    elif 'pt' in var:
                        model = (f'WP{i}_{region}_{pf}_{particle}_{var}','',100,200,1200)
                    elif ('particleNet_mass' in var) or ('softdrop' in var):
                        model = (f'WP{i}_{region}_{pf}_{particle}_{var}','',60,0,300)

                    print(f'Making plot of {model[0]}')
                    if isData:
                        hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}')
                    else:
                        hTemp = selection.a.DataFrame.Histo1D(model,f'{particle}_{var}',weight_col)
                    hTemp.SetDirectory(0)
                    controlPlots.append(hTemp)

            for mxmy in [f'mhww_WP{i}',f'mww_WP{i}',f'mhww_WP{i}_nocorr',f'mww_WP{i}_nocorr']:
                mass = mxmy.split('_')[0] + ('_nocorr' if '_nocorr' in mxmy else '')
                model = (f'WP{i}_{region}_{pf}_{mass}','',100,0,3000)
                print(f'Making plot of {model[0]}')
                if isData:
                    hTemp = selection.a.DataFrame.Histo1D(model,mxmy)
                else:
                    hTemp = selection.a.DataFrame.Histo1D(model,mxmy,weight_col)
                hTemp.SetDirectory(0)
                controlPlots.append(hTemp)


fOut = ROOT.TFile.Open(f'rootfiles/CR_SR_studies_{args.setname}_{args.era}.root','RECREATE')
fOut.cd()
for plot in controlPlots:
    print(f'Writing {plot.GetName()} to file....')
    if 'GenMatch' in plot.GetName():
        nBin = 1
        for code, name in statuses.items():
            plot.GetXaxis().SetBinLabel(nBin,name)
            nBin += 1

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
