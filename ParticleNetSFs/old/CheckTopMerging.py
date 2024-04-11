'''
Script to perform basic gen matching for tops and define columns for the various top matching criteria.
'''
import ROOT
from TIMBER.Analyzer import Correction, HistGroup, CutGroup, VarGroup, ModuleWorker, analyzer
from TIMBER.Tools.Common import CompileCpp
from XHYbbWW_class import XHYbbWW

def analyze(selection):
    '''
    # find all Ws and bs, store their mothers' indices and their pT, eta, phi
    selection.a.Define("GenB_genPartIdxMother","GenPart_genPartIdxMother[GenPart_pdgId == 5 or GenPart_pdgId == -5]")
    selection.a.Define("GenW_genPartIdxMother","GenPart_genPartIdxMother[GenPart_pdgId == 24 or GenPart_pdgId == -24]")
    # find mothers' PDG ids
    selection.a.Define("GenB_pdgIdMother","FindMothersPdgId(GenPart_pdgId,GenB_genPartIdxMother)")
    selection.a.Define("GenW_pdgIdMother","FindMothersPdgId(GenPart_pdgId,GenW_genPartIdxMother)")

    # find those whose mothers are tops and make new subcollections for each
    # afterwards, there will be columns called 
    #	- GenWfromTop_idx
    #	- GenBfromTop_idx
    selection.a.SubCollection('GenBfromTop','GenPart','abs(GenB_pdgIdMother) == 6')
    selection.a.SubCollection('GenWfromTop','GenPart','abs(GenW_pdgIdMother) == 6')

    # find the light quarks whose mothers are GenWfromTop
    selection.a.Define('GenQ_genPartIdxMother','GenPart_genPartIdxMother[abs(GenPart_pdgId) >= 1 and abs(GenPart_pdgId) < 6]')
    selection.a.SubCollection('GenQfromWfromTop','GenPart','GenQ_genPartIdxMother == GenWfromTop_idx')
    '''

    selection.a.Define("GenW_genPartIdxMother","GenPart_genPartIdxMother[GenPart_pdgId == 24 or GenPart_pdgId == -24]")
    selection.a.Define("GenW_pdgIdMother","FindMothersPdgId(GenPart_pdgId,GenW_genPartIdxMother)")


    # find generator tops. Will produce column called GenTop_idx
    selection.a.SubCollection('GenTop','GenPart','abs(GenPart_pdgId) == 6')
    selection.a.Define("junk", "std::cout << rdfslot_ << std::endl; return 0;")
    a = selection.a.GetActiveNode().DataFrame.Count().GetValue()
    print(a)

    # find Ws not from tops
    selection.a.SubCollection('GenWnoTop','GenPart','abs(GenW_pdgIdMother) != 6')
    selection.a.Define("junk2", "std::cout << rdfslot_ << std::endl; return 0;")
    a = selection.a.GetActiveNode().DataFrame.Count().GetValue()
    print(a)

    # find Higgses
    selection.a.SubCollection('GenH','GenPart','abs(GenPart_pdgId) == 25')
    selection.a.Define("junk3", "std::cout << rdfslot_ << std::endl; return 0;")
    a = selection.a.GetActiveNode().DataFrame.Count().GetValue()
    print(a)

    selection.a.Define('jet_0','ROOT::Math::PtEtaPhiMVector(Trijet_pt[0],Trijet_eta[0],Trijet_phi[0],Trijet_msoftdrop[0])')
    selection.a.Define('jet_1','ROOT::Math::PtEtaPhiMVector(Trijet_pt[1],Trijet_eta[1],Trijet_phi[1],Trijet_msoftdrop[1])')
    selection.a.Define('jet_2','ROOT::Math::PtEtaPhiMVector(Trijet_pt[2],Trijet_eta[2],Trijet_phi[2],Trijet_msoftdrop[2])')
    selection.a.Define("junk4", "std::cout << rdfslot_ << std::endl; return 0;")
    a = selection.a.GetActiveNode().DataFrame.Count().GetValue()
    print(a)

    # determine which of the three jets are assiciated with which gen particle by dR match
    selection.a.Define('GenMatchStatus','GenMatchingLoop(jet_0, jet_1, jet_2, GenTop_pt, GenTop_eta, GenTop_phi, GenTop_mass, GenWnoTop_pt, GenWnoTop_eta, GenWnoTop_phi, GenWnoTop_mass, GenH_pt, GenH_eta, GenH_phi, GenH_mass)')
    selection.a.Define("junk5", "std::cout << rdfslot_ << std::endl; return 0;")
    a = selection.a.GetActiveNode().DataFrame.Count().GetValue()
    print(a)

    # At this point, we have four collections:
    #	- GenTop
    #	  - GenBfromTop
    #	  - GenWfromTop
    #	    - GenQfromWfromTop
    # We will call a function that checks the merging status
    #selection.a.Define('TopMergingStatus','TopMergingStatus(GenTop_phi,GenBfromTop_phi,GenQfromWfromTop_phi)')


    #selection.a.Snapshot(['GenMatchStatus'],'out_snapshot.root','Events')

    print(selection.a.GetCollectionNames())

    out = ROOT.TFile.Open('out.root','RECREATE')
    out.cd()
    h = selection.a.DataFrame.Histo1D(('h','h',5,-1,4),'GenMatchStatus')
    h.Write()
    out.Close()

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
                        action='store', required=True,
                        help='Setname to process.')
    parser.add_argument('-y', type=str, dest='year',
                        action='store', required=True,
                        help='Year of set (16APV, 16, 17, 18).')
    '''
    parser.add_argument('-t', type=str, dest='tagger',
                        help='Exact name of tagger discriminant, e.g "Trijet_particleNetMD_HbbvsQCD", "Trijet_particleNetMD_WvsQCD"',
                        action='store', required=True)
    parser.add_argument('-w', type=float, dest='wp',
                        help='tagger working point',
                        action='store', required=True)
    '''
    args = parser.parse_args()

    CompileCpp('ParticleNetSFs/TopMerging.cc')

    filename = 'trijet_nano/{}_{}_snapshot.txt'.format(args.setname,args.year)
    selection = XHYbbWW('trijet_nano/{}_{}_snapshot.txt'.format(args.setname,args.year),args.year,1,1)

    analyze(selection)
