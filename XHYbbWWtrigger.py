import sys, time, ROOT, subprocess, os
from collections import OrderedDict

from TIMBER.Analyzer import HistGroup
from TIMBER.Tools.Common import CompileCpp, ExecuteCmd

from XHYbbWW_class import XHYbbWW

def HaddData(year):
    '''
    hadd all of the data snapshots and backfill any empty trigger entries from sub-year eras.
    '''
    files = subprocess.check_output('ls ../trijet_nano_files/',shell=True)
    # check if the hadd-ed XHYbbWWsnapshot_Data_YEAR exists yet. If not, create it
    exists = False
    for f in files.split('\n'):
	if str(year) in f:
	    exists = True
    if not exists:
	# for now, just move the offending files from the snapshots directory. The only problematic ones are DataB (2016)
	'''
	# DataB1 is broken for 2016, skip them 
	if year == 16:
	    subyears = ['B','B2','C','D','E','F','G','H']
	    haddstr = ''
	    for sy in subyears:
	        haddstr += '../trijet_nano_files/snapshots/HWWsnapshot_Data{}_{}_*.root '.format(sy, year)
	    ExecuteCmd('hadd -f ../trijet_nano_files/XHYbbWWsnapshot_Data_{}.root {}'.format(year,haddstr))
	else:
	    ExecuteCmd('hadd -f ../trijet_nano_files/XHYbbWWsnapshot_Data_{0}.root ../trijet_nano_files/snapshots/HWWsnapshot_Data*_{0}_*.root'.format(year))
	'''
	ExecuteCmd('hadd -f ../trijet_nano_files/XHYbbWWsnapshot_Data_{0}.root ../trijet_nano_files/snapshots/HWWsnapshot_Data*_{0}_*.root'.format(year))
    else:
	print('../trijet_nano_files/XHYbbWWsnapshot_Data_{0}.root exists already, skipping...'.format(year))


def MakeEfficiency(year):
    selection = XHYbbWW('../trijet_nano_files/XHYbbWWsnapshot_Data_{}.root'.format(year),year,1,1)

    # debugging 
    #selection = XHYbbWW('../trijet_nano_files/snapshots/HWWsnapshot_DataH_16_44of50.root',year,1,1)

    selection.OpenForSelection('None')
    hists = HistGroup('out')

    noTag = selection.a.Cut('pretrig','HLT_PFJet320==1')

    # Baseline - no tagging
    hists.Add('preTagDenominator',selection.a.DataFrame.Histo1D(('preTagDenominator','',22,800,3000),'mhww_trig'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator',selection.a.DataFrame.Histo1D(('preTagNumerator','',22,800,3000),'mhww_trig'))

    # Make efficieincies
    effs = {
        "Pretag": ROOT.TEfficiency(hists['preTagNumerator'], hists['preTagDenominator'])
    }

    out = ROOT.TFile.Open('HWWtrigger_%s.root'%year,'RECREATE')
    out.cd()
    for name,eff in effs.items():
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


if __name__ == '__main__':
    start = time.time()
    #CompileCpp('THmodules.cc')
    for y in [16,17,18]:
	HaddData(y)
        MakeEfficiency(y)

    files = {
        16: ROOT.TFile.Open('HWWtrigger_16.root'),
        17: ROOT.TFile.Open('HWWtrigger_17.root'),
        18: ROOT.TFile.Open('HWWtrigger_18.root')
    }

    hists = {hname.GetName():[files[y].Get(hname.GetName()) for y in [16,17,18]] for hname in files[16].GetListOfKeys() if '_graph' in hname.GetName()}
    colors = [ROOT.kBlack, ROOT.kGreen+1, ROOT.kOrange-3]
    legendNames = ['2016','2017','2018']
    for hname in hists.keys():
        c = ROOT.TCanvas('c','c',800,700)
        leg = ROOT.TLegend(0.7,0.5,0.88,0.7)
        for i,h in enumerate(hists[hname]):
            h.SetLineColor(colors[i])
            h.SetTitle('')
<<<<<<< HEAD
            h.GetXaxis().SetTitle('m_{jj}')
=======
            h.GetXaxis().SetTitle('m_{HWW}')
>>>>>>> ae17b90b4c06965f48dd3eb4dc863183f82eb216
            h.GetYaxis().SetTitle('Efficiency')
            if i == 0:
                h.Draw('AP')
            else:
                h.Draw('same P')
            
            leg.AddEntry(h,legendNames[i],'pe')

        leg.Draw()
        c.Print('plots/Trigger_%s.pdf'%hname,'pdf')

    print ('%s sec'%(time.time()-start))

