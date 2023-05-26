import sys, time, ROOT, subprocess, os
from collections import OrderedDict

from TIMBER.Analyzer import HistGroup
from TIMBER.Tools.Common import CompileCpp, ExecuteCmd

from XHYbbWW_class import XHYbbWW

def MakeEfficiency(year, HT=0):
    '''
	year (str) : 16, 17, 17B, 17All, 18
	HT   (int) : value of HT to cut on 
	For measuring trigger efficiencies, we use the data from the orthogonal SingleMuon dataset.
    '''
    # 2017 might have to be split up due to 2017B not having certain jet substructure triggers
    if year == '17B':
	fName = 'trijet_nano/SingleMuonDataB_17_snapshot.txt'
    elif year == '17All':
	fName = 'trijet_nano/SingleMuonDataWithB_17_snapshot.txt'
    else:
	fName = 'trijet_nano/SingleMuonData_{}_snapshot.txt'.format(year)
    print('-------------------------- {} : {} --------------------------------------------'.format(fName,year))

    selection = XHYbbWW(fName,year if year.isdigit() else '17',1,1)
    selection.OpenForSelection('None')
    hists = HistGroup('out')

    # keep track of total efficiency to see how HT cut affects it
    before = selection.a.DataFrame.Count()
    # cut on HT to improve trigger efficiency
    selection.a.Cut('HT_cut', 'HT > {}'.format(HT))
    after = selection.a.DataFrame.Count()

    noTag = selection.a.Cut('pretrig','HLT_Mu50==1')

    # Baseline - no tagging
    hists.Add('preTagDenominator',selection.a.DataFrame.Histo1D(('preTagDenominator','',22,800,3000),'mhww_trig'))
    hists.Add('HTDenominator',selection.a.DataFrame.Histo1D(('HTDenominator','',22,800,3000),'HT'))
    hists.Add('preTagDenominator_mjavg',selection.a.DataFrame.Histo1D(('preTagDenominator_mjavg','',20,60,260),'m_javg'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator',selection.a.DataFrame.Histo1D(('preTagNumerator','',22,800,3000),'mhww_trig'))
    hists.Add('HTNumerator',selection.a.DataFrame.Histo1D(('HTNumerator','',22,800,3000),'HT'))
    hists.Add('preTagNumerator_mjavg',selection.a.DataFrame.Histo1D(('preTagNumerator_mjavg','',20,60,260),'m_javg'))

    # Make efficieincies
    effs = {
        "Pretag": ROOT.TEfficiency(hists['preTagNumerator'], hists['preTagDenominator']),
	"Pretag_mjavg": ROOT.TEfficiency(hists['preTagNumerator_mjavg'], hists['preTagDenominator_mjavg']),
	"HT": ROOT.TEfficiency(hists['HTNumerator'], hists['HTDenominator'])
    }

    out = ROOT.TFile.Open('triggers/HWWtrigger_HT{}_{}.root'.format(HT,year),'RECREATE')
    out.cd()
    for name,eff in effs.items():
	print('Processing {}'.format(name))
        f = ROOT.TF1("eff_func","-[0]/10*exp([1]*x/1000)+1",800,2600)
        f.SetParameter(0,1)
        f.SetParameter(1,-2)
        eff.Fit(f)
        eff.Write()
        g = eff.CreateGraph()
        g.SetName(name+'_graph')
        g.SetTitle(name)
        g.SetMinimum(0.5)
        g.SetMaximum(1.01)
        g.Write()
    out.Close()

    before = before.GetValue()
    after = after.GetValue()
    print('------------------------------------------------------------')
    print('Cut on HT > {} removes {}% of SingleMuon data in 20{}'.format(HT, 100.*(1.-(float(after)/float(before))), year))
    print('------------------------------------------------------------')

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--HT', type=str, dest='HT',
			action='store', default='0',
			 help='Value of HT to cut on')
    args = parser.parse_args()

    start = time.time()
    #CompileCpp('THmodules.cc')
    for y in ['16','17','17B','17All','18']:
        MakeEfficiency(y, args.HT)

    files = {
        '16': ROOT.TFile.Open('triggers/HWWtrigger_HT{}_16.root'.format(args.HT)),
        '17': ROOT.TFile.Open('triggers/HWWtrigger_HT{}_17.root'.format(args.HT)),		# contains 2017 C,D,E,F
        '18': ROOT.TFile.Open('triggers/HWWtrigger_HT{}_18.root'.format(args.HT)),
	'17B': ROOT.TFile.Open('triggers/HWWtrigger_HT{}_17B.root'.format(args.HT)),		# contains 2017 B
	'17All': ROOT.TFile.Open('triggers/HWWtrigger_HT{}_17All.root'.format(args.HT))	# contains 2017 B,C,D,E,F
    }

    hists = {hname.GetName():[files[y].Get(hname.GetName()) for y in ['16','17','18']] for hname in files['16'].GetListOfKeys() if '_graph' in hname.GetName()}
    colors = [ROOT.kBlack, ROOT.kGreen+1, ROOT.kOrange-3]
    legendNames = ['2016','2017','2018']
    for hname in hists.keys():
        c = ROOT.TCanvas('c','c',800,700)
        leg = ROOT.TLegend(0.7,0.5,0.88,0.7)
        for i,h in enumerate(hists[hname]):
            h.SetLineColor(colors[i])
            h.SetTitle('')
            if 'HT' in hname: 
		h.GetXaxis().SetTitle('H_{T}')
	    else:
		h.GetXaxis().SetTitle('m_{jjj}')
            h.GetYaxis().SetTitle('Efficiency')
            if i == 0:
                h.Draw('AP')
            else:
                h.Draw('same P')
            
            leg.AddEntry(h,legendNames[i],'pe')

        leg.Draw()
        c.Print('plots/Trigger_{}_HTCut{}.pdf'.format(hname,args.HT),'pdf')

    c.Clear()
    # Now compare just 2017 total (B,C,D,E,F) and 2017 later (C,D,E,F)
    leg2 = ROOT.TLegend(0.7,0.5,0.88,0.7)
    # total 2017 minus 2017B
    h17 = files['17'].Get('Pretag_graph')
    h17.SetLineColor(ROOT.kGreen)
    h17.SetTitle('')
    h17.GetXaxis().SetTitle('m_{jjj}')
    h17.GetYaxis().SetTitle('Efficiency')
    h17.Draw('AP')
    leg2.AddEntry(h17, 'later 2017', 'pe')

    # only 2017B
    h17B = files['17B'].Get('Pretag_graph')
    h17B.SetLineColor(ROOT.kBlack)
    h17B.SetTitle('')
    h17B.GetXaxis().SetTitle('m_{jjj}')
    h17B.GetYaxis().SetTitle('Efficiency')
    h17B.Draw('same P')
    leg2.AddEntry(h17B, 'full 2017', 'pe')

    leg2.Draw()
    c.Print('plots/Trigger_2017Full_vs_2017Later_pretag_HT{}.pdf'.format(args.HT))

    print ('%s sec'%(time.time()-start))

