'''
Script to measure the trigger efficiency in the semi-leptonic ttbar MC and compare to data.
'''

import sys, time, ROOT
from collections import OrderedDict
from TIMBER.Analyzer import HistGroup
from TIMBER.Tools.Common import CompileCpp
from XHYbbWW_class import XHYbbWW

def MakeEfficiency(year, HT=0):
    tt = 'trijet_nano/ttbar-semilep_{}_snapshot.txt'.format(year)
    data = 'trijet_nano/SingleMuonData_{}_snapshot.txt'.format(year)

    tt_sel = XHYbbWW(tt, year, 1, 1)
    data_sel = XHYbbWW(data, year, 1, 1)

    hists = HistGroup('out')
    effs = {}

    for var in [tt_sel, data_sel]:
	if var == tt_sel:
	    name = 'tt-semilep'
	else:
	    name = 'singlemu-data'
	var.OpenForSelection('None')
	notag = getattr(var.a, 'Cut')('pretrig','HLT_Mu50==1')
	histo2D = getattr(var.a.DataFrame, 'Histo2D')
	hists.Add('pretag_denominator_%s'%name,histo2D(('pretag_denominator','pretag_denomenator',22,800,3000,20,60,260),'mhww_trig','m_javg'))
	var.ApplyTrigs(applyToMC=True)
	hists.Add('pretag_numerator_%s'%name,histo2D(('pretag_numerator','pretag_numerator',22,800,3000,20,60,260),'mhww_trig','m_javg'))
	effs['pretag_%s'%name] = ROOT.TEfficiency(hists['pretag_numerator_%s'%name], hists['pretag_denominator_%s'%name])

    out = ROOT.TFile.Open('triggers/TTsemilep_vs_singleMuon_HT{}_{}.root'.format(HT,year),'RECREATE')
    out.cd()
    for name, eff in effs.items():
        g = eff.CreateHistogram()
        g.SetName(name+'_hist')
        g.SetTitle(name)
        g.GetXaxis().SetTitle('m_{jjj} (GeV)')
     	g.GetYaxis().SetTitle('m_{j}^{avg} (GeV)')
        g.GetZaxis().SetTitle('Efficiency')
        g.SetMinimum(0.6)
        g.SetMaximum(1.0)
        g.Write()
        eff.SetName(name)
        eff.Write()
    out.Close()	

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--HT', type=str, dest='HT',
                        action='store', default='0',
                         help='Value of HT to cut on')
    parser.add_argument('--recycle', dest='recycle',
                        action='store_true', default=False,
                        help='Recycle existing files and just plot.')
    args = parser.parse_args()
    start = time.time()
    #CompileCpp('THmodules.cc')
    if not args.recycle:
        for y in ['16','17','18']:
            MakeEfficiency(y, args.HT)
