'''
Script to make the tagger efficiencies for a given process, tagger, and working point
'''
import ROOT
from TIMBER.Analyzer import Correction, HistGroup, CutGroup, VarGroup, ModuleWorker, analyzer
from TIMBER.Tools.Common import CompileCpp
from XHYbbWW_class import XHYbbWW

def analyze(selection, args):
    # Define an RVec<int> with the gen matching status for each of the three jets in every event
    # 1: qq, 2: bq, 3:bqq, 4:Higgs, 5:W(not from top), 0:other
    #selection.a.Define('jetCat0','classifyProbeJet(0, Trijet_phi, Trijet_eta, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother)')
    #selection.a.Define('jetCat1','classifyProbeJet(1, Trijet_phi, Trijet_eta, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother)')
    #checkpoint = selection.a.Define('jetCat2','classifyProbeJet(2, Trijet_phi, Trijet_eta, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother)')

    checkpoint = selection.a.Define('jetCats','classifyProbeJets({0,1,2}, Trijet_phi, Trijet_eta, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother)')

    # Now, determine the tagging efficiencies for each type of matched jet
    statuses = {'other':0, 'top_qq':1, 'top_bq':2, 'top_bqq':3, 'Higgs':4, 'W':5}
    outName = 'ParticleNetSFs/EfficiencyMaps/%s_%s_Efficiencies.root'%(selection.setname,selection.year)
    outFile = ROOT.TFile.Open(outName,'RECREATE')
    outFile.cd()

    # Book a histgroup to store the kinematic distribution plots for each category
    hists = HistGroup('kinematic_plots')
    for matching, statuscode in statuses.items():
        print('Plotting mass distribution for gen-matched %s cands'%matching)
        selection.a.SetActiveNode(checkpoint)
        selection.a.SubCollection('GenMatched_%s_Jets'%matching, 'Trijet', 'jetCats == %s'%statuscode)
        # Mass distributions
        mass = selection.a.GetActiveNode().DataFrame.Histo1D(('GenMatched_%s_mass'%matching,'GenMatched_%s_mass'%matching,100,0,300),'GenMatched_%s_Jets_mregressed_corr'%(matching))
        hists.Add('GenMatched_%s_Jets_mass'%matching, mass)
        # pT distributions
        pt = selection.a.GetActiveNode().DataFrame.Histo1D(('GenMatched_%s_pt'%matching,'GenMatched_%s_pt'%matching,100,0,1000),'GenMatched_%s_Jets_pt_corr'%(matching))
        hists.Add('GenMatched_%s_Jets_pT'%matching, pt)
        # score distributions 
        for tagger in ['particleNetMD_HbbvsQCD','particleNetMD_WvsQCD','particleNet_TvsQCD']:
            score = selection.a.GetActiveNode().DataFrame.Histo1D(('GenMatched_%s_%s_score'%(matching,tagger),'GenMatched_%s_%s_score'%(matching,tagger),50,0,1),'GenMatched_%s_Jets_%s'%(matching,tagger))
            hists.Add('GenMatched_%s_Jets_%s_score'%(matching,tagger), score)


    for tagger in ['Trijet_particleNetMD_HbbvsQCD','Trijet_particleNetMD_WvsQCD','Trijet_particleNet_TvsQCD']:
        for matching, statuscode in statuses.items():
            if 'HbbvsQCD' in tagger: wp = 0.98
            elif 'WvsQCD' in tagger: wp = 0.80
            elif 'TvsQCD' in tagger: wp = 0.94

            print('Obtaining tagging efficiency for %s-matched jets using %s tagger'%(matching,tagger))
            selection.a.SetActiveNode(checkpoint)

            selection.a.SubCollection('%sJets_all_%s'%(matching,tagger),'Trijet','jetCats == %s'%statuscode)
            selection.a.SubCollection('%sJets_tag_%s'%(matching,tagger),'Trijet','jetCats == %s && %s > %s'%(statuscode,tagger,wp))

            denominator = selection.a.GetActiveNode().DataFrame.Histo2D(('%s_%s_d'%(matching,tagger),'denominator',4,300,1500,4,-2.4,2.4),'%sJets_all_%s_pt_corr'%(matching,tagger),'%sJets_all_%s_eta'%(matching,tagger)).GetValue()
            numerator   = selection.a.GetActiveNode().DataFrame.Histo2D(('%s_%s_n'%(matching,tagger),'numerator',4,300,1500,4,-2.4,2.4),'%sJets_tag_%s_pt_corr'%(matching,tagger),'%sJets_tag_%s_eta'%(matching,tagger)).GetValue()

            print('Creating TEfficiency for (jetCat == {0} && {1} > {2})/(jetCat == {0})'.format(matching,tagger,wp))
            eff = ROOT.TEfficiency(numerator,denominator)
            hist = eff.CreateHistogram()
            hist.SetTitle('%s-matched_%s_WP%s_eff'%(matching,tagger,str(wp).replace('.','p')))
            hist.SetName('%s-matched_%s_WP%s_eff'%(matching,tagger,str(wp).replace('.','p')))
            eff.SetTitle('%s-matched_%s_WP%s_TEff'%(matching,tagger,str(wp).replace('.','p')))
            eff.SetName('%s-matched_%s_WP%s_TEff'%(matching,tagger,str(wp).replace('.','p')))
            eff.Write()
            hist.Write()
            eff.SetDirectory(0)
            hist.SetDirectory(0)

    print('Writing kinematic histograms...')
    hists.Do('Write')
    outFile.Close()


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
                        action='store', required=True,
                        help='Setname to process.')
    parser.add_argument('-y', type=str, dest='year',
                        action='store', required=True,
                        help='Year of set (16APV, 16, 17, 18).')

    #verbosity = ROOT.Experimental.RLogScopedVerbosity(ROOT.Detail.RDF.RDFLogChannel(), ROOT.Experimental.ELogLevel.kInfo)

    args = parser.parse_args()

    CompileCpp('ParticleNetSFs/TopMergingFunctions.cc')

    filename = 'trijet_nano/{}_{}_snapshot.txt'.format(args.setname,args.year)
    selection = XHYbbWW('trijet_nano/{}_{}_snapshot.txt'.format(args.setname,args.year),args.year,1,1)
    selection.OpenForSelection('None')
    selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else str(selection.GetXsecScale()))

    analyze(selection, args)
