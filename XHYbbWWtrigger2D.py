import sys, time, ROOT
from collections import OrderedDict

from TIMBER.Analyzer import HistGroup
from TIMBER.Tools.Common import CompileCpp

from XHYbbWW_class import XHYbbWW

def MakeEfficiency(year):
    '''
        year (str) : 16, 17, 17B, 17All, 18
    '''
    if year == '17B':
        fName = 'trijet_nano/SingleMuonDataB_17_snapshot.txt'
    elif year == '17All':
        fName = 'trijet_nano/SingleMuonDataWithB_17_snapshot.txt'
    else:
        fName = 'trijet_nano/SingleMuonData_{}_snapshot.txt'.format(year)

    selection = XHYbbWW(fName,year if year.isdigit() else '17',1,1)
    selection.OpenForSelection('None')
    hists = HistGroup('out')

    noTag = selection.a.Cut('pretrig','HLT_Mu50==1')

    # Baseline - no tagging
    hists.Add('preTagDenominator',selection.a.DataFrame.Histo2D(('preTagDenominator','',20,60,260,22,800,3000),'m_javg','mhww_trig'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator',selection.a.DataFrame.Histo2D(('preTagNumerator','',20,60,260,22,800,3000),'m_javg','mhww_trig'))

    effs = {
        "Pretag": ROOT.TEfficiency(hists['preTagNumerator'], hists['preTagDenominator'])
    }

    out = ROOT.TFile.Open('HWWtrigger2D_%s.root'%year,'RECREATE')

    out.cd()
    for name,eff in effs.items():
        g = eff.CreateHistogram()
        g.SetName(name+'_hist')
        g.SetTitle(name)
        g.GetXaxis().SetTitle('m_{j}^{avg} (GeV)')
        g.GetYaxis().SetTitle('m_{jj} (GeV)')
        g.GetZaxis().SetTitle('Efficiency')
        g.SetMinimum(0.6)
        g.SetMaximum(1.0)
        f = ROOT.TF2("eff_func","1-[0]/10*exp([1]*y/1000)*exp([2]*x/200)",60,260,800,2600)
        f.SetParameter(0,1)
        f.SetParameter(1,-2)
        f.SetParameter(2,-2)
        g.Fit(f)
        g.Write()
        eff.SetName(name)
        eff.Write()
    out.Close()

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--recycle', dest='recycle',
                        action='store_true', default=False,
                        help='Recycle existing files and just plot.')
    args = parser.parse_args()
    start = time.time()
    #CompileCpp('THmodules.cc')
    if not args.recycle:
        for y in ['16','17','18']:
            MakeEfficiency(y)

    files = {
        '16': ROOT.TFile.Open('HWWtrigger2D_16.root'),
        '17': ROOT.TFile.Open('HWWtrigger2D_17.root'),
        '18': ROOT.TFile.Open('HWWtrigger2D_18.root'),
	'17B': ROOT.TFile.Open('HWWtrigger2D_17B.root'),
	'17All': ROOT.TFile.Open('HWWtrigger2D_17All.root')
    }

    hists = {hname.GetName():[files[y].Get(hname.GetName()) for y in ['16','17','18']] for hname in files['16'].GetListOfKeys() if '_hist' in hname.GetName()}
    colors = [ROOT.kBlack, ROOT.kGreen+1, ROOT.kOrange-3]
    legendNames = ['2016','2017','2018']
    for hname in hists.keys():
        c = ROOT.TCanvas('c','c',2000,700)
        c.Divide(3,1)
        for i,h in enumerate(hists[hname]):
            c.cd(i+1)
            ROOT.gPad.SetLeftMargin(0.13)
            ROOT.gPad.SetRightMargin(0.16)
            h.GetZaxis().SetTitleOffset(1.7)
            h.SetLineColor(colors[i])
            h.SetTitle(legendNames[i])
            h.Draw('colz')

        c.Print('plots/Trigger2D_%s.pdf'%hname,'pdf')

    print ('%s sec'%(time.time()-start))
