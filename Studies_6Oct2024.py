'''
Script for studying / remaking event selection for X->HY-bbWW (semi-resolved)
'''
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

#########################################################################################################
#                       STAGE 1 : control plots before any tagger cuts                                  #
#########################################################################################################
for iJet in range(3):
    for property in ['mregressed_corr','pt_corr','particleNetMD_WvsQCD','particleNetMD_HbbvsQCD']:
        print(f'STAGE 1: pre-tagger-cuts : {property} Jet {iJet}')
        selection.a.Define(f'Jet{iJet}_{property}',f'Trijet_{property}[{iJet}]')
        if 'mregressed' in property:
            model = (f"STAGE1_{property}_{iJet}",f"{property} Jet {iJet}",60,0,300)
        elif 'pt' in property:
            model = (f"STAGE1_{property}_{iJet}",f"{property} Jet {iJet}",100,200,2200)
        elif 'particleNet' in property:
            model = (f"STAGE1_{property}_{iJet}",f"{property} Jet {iJet}",50,0,1)
        hTemp = selection.a.DataFrame.Histo1D(model,f'Jet{iJet}_{property}',"weight__nominal")
        hTemp.SetDirectory(0)
        controlPlots.append(hTemp)
h_mx = selection.a.DataFrame.Histo1D(
    ('STAGE1_mx','mx pre-tag',100,0,3000),
    'mhww_msoftdrop_trig_corr',
    'weight__nominal'
)
h_mx.SetDirectory(0)
controlPlots.append(h_mx)
h_my = selection.a.DataFrame.Histo1D(
    ('STAGE1_my','my pre-tag',100,0,3000),
    'm_javg_softdrop_corr',
    'weight__nominal'
)
h_my.SetDirectory(0)
controlPlots.append(h_my)

#########################################################################################################
#                       STAGE 1 : control plots before any tagger cuts                                  #
#########################################################################################################
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
    print('----------------------------------------------------------------------')
    print(f'Selecting two candidate Ws using MD_WvsQCD working point {wp}')
    #print(selection.getNweighted().GetValue())
    print('----------------------------------------------------------------------')
    name = str(wp).replace('.','p')
    objIdxs = f'ObjIdxs_{name}'
    selection.a.Define(
        objIdxs,
        'Pick_W_candidates_standard(%s, %s, %s, {0, 1, 2}, %s)'%(
            'Trijet_particleNetMD_WvsQCD',
            wp,
            'false', # enables W tagging instead of anti-tagging
            123456  # lower bound on W anti-tag (not relevant, only used in CR)
        )
    )
    #selection.a.DataFrame.Display([objIdxs]).Print()
    selection.a.Define(f'w1Idx','{}[0]'.format(objIdxs))
    selection.a.Define(f'w2Idx','{}[1]'.format(objIdxs))
    selection.a.Define(f'hIdx', '{}[2]'.format(objIdxs))
    selection.a.Cut('Has2Ws',f'(w1Idx > -1) && (w2Idx > -1) && (hIdx > -1)')
    #print(selection.getNweighted().GetValue())
    cols_to_skip = ['vect_msoftdrop','vect_mregressed','vect_msoftdrop_corr','vect_mregressed_corr','tau2','tau3','tau1','tau4','particleNetMD_QCD','deepTagMD_HbbvsQCD','particleNet_TvsQCD','particleNetMD_Xcc','deepTagMD_WvsQCD','particleNet_QCD','jetId','particleNetMD_Xbb','particleNet_WvsQCD','deepTagMD_ZHbbvsQCD','deepTag_TvsQCD','rawFactor','particleNetMD_Xqq']
    #print(selection.getNweighted().GetValue())
    cols = ['Trijet_%s'%i for i in cols_to_skip]
    selection.a.ObjectFromCollection(f'W1','Trijet',f'w1Idx',skip=cols)
    selection.a.ObjectFromCollection(f'W2','Trijet',f'w2Idx',skip=cols)
    selection.a.ObjectFromCollection(f'H','Trijet',f'hIdx',skip=cols)
    # now make some control plots 
    for jet in ['W1','W2','H']:
        for property in ['mregressed_corr','pt_corr','particleNetMD_WvsQCD','particleNetMD_HbbvsQCD']:
            print(f'STAGE {i+2}: post-W-tagger-cuts (WP {wp}) : {jet} jet {property}')
            if 'mregressed' in property:
                model = (f"STAGE{i+2}_{property}_{jet}",f"{property} Jet {jet}",60,0,300)
            elif 'pt' in property:
                model = (f"STAGE{i+2}_{property}_{jet}",f"{property} Jet {jet}",100,200,2200)
            elif 'particleNet' in property:
                model = (f"STAGE{i+2}_{property}_{jet}",f"{property} Jet {jet}",50,0,1)
            hTemp = selection.a.DataFrame.Histo1D(model,f'{jet}_{property}',"weight__nominal")
            hTemp.SetDirectory(0)
            controlPlots.append(hTemp)


fOut = ROOT.TFile.Open(f'rootfiles/Studies_{args.setname}_{args.era}_var{args.variation}.root','RECREATE')
fOut.cd()
for plot in controlPlots:
    print(f'Writing {plot.GetTitle()} to file...')
    plot.Write()
fOut.Close()