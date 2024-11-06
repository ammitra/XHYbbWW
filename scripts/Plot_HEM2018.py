'''
Script to plot the full 2018 dataset before and after applying the HEM correction
'''
from collections import OrderedDict
from XHYbbWW_class import XHYbbWW
from TIMBER.Analyzer import Correction, CutGroup, ModuleWorker, analyzer
from argparse import ArgumentParser
import ROOT


def plot(proc):
    print(f'Running over {proc} 2018 dataset....')
    selection = XHYbbWW(f'trijet_nano/{proc}_18_snapshot.txt','18',1,1)

    nBefore = selection.getNweighted()

    HEM_worker = ModuleWorker(f'HEM_veto','TIMBER/Framework/include/HEM_veto.h',[proc])
    if 'Data' in proc:
        selection.a.Cut(f'HEM_veto_{proc}','%s == 0'%(HEM_worker.GetCall(evalArgs={"FatJet_eta":"Trijet_eta","FatJet_phi":"Trijet_phi","run":"run"})))
    else:
        selection.a.Cut(f'HEM_veto_{proc}','%s == 0'%(HEM_worker.GetCall(evalArgs={"FatJet_eta":"Trijet_eta","FatJet_phi":"Trijet_phi"})))

    nAfter = selection.getNweighted()

    if 'Data' not in proc:
        selection.OpenForSelection('None',runCorrs=True)
        selection.a.MakeWeightCols(
            correctionNames = list(selection.a.GetCorrectionNames()),
            extraNominal = f'{selection.GetXsecScale()}'
        )
        hist = selection.a.DataFrame.Histo2D(
            (f'{proc}',f'{proc}',70,-3,3,70,-3.14,-3.14),
            "Trijet_eta","Trijet_phi",
            "weight__nominal"
        )
    else:
        hist = selection.a.DataFrame.Histo2D(
            (f'{proc}',f'{proc}',70,-3,3,70,-3.14,-3.14),
            "Trijet_eta","Trijet_phi"
        )


    # Plot
    c = ROOT.TCanvas(f'{proc}',f'{proc}',800,800)
    c.cd()
    hist.SetStats(0)
    hist.SetTitle(f'{proc} 2018 after HEM veto')
    hist.GetXaxis().SetTitle('#eta')
    hist.GetYaxis().SetTitle('#phi')
    hist.Draw('colz')
    c.Print(f'plots/{proc}_2018_HEM_veto.pdf')

    ratio = nAfter.GetValue()/nBefore.GetValue()
    print(f'\tLoss of {1.-(ratio*100.)}% events after HEM veto')

parser = ArgumentParser()
parser.add_argument('-s', type=str, dest='setname',
                    action='store', required=True,
                    help='Setname to process.')
args = parser.parse_args()

proc = args.setname

plot(proc)
