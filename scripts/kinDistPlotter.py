import ROOT
from TIMBER.Analyzer import analyzer, HistGroup
from TIMBER.Tools.Plot import *
from collections import OrderedDict

samples = {
	"ttbar" : "t#bar{t}",
	"QCD"	: "QCD",
	"MX1800-MY125_17": "(1800,125)"
}

colors = {'ttbar':ROOT.kRed,'QCD':ROOT.kYellow,'MX1800-MY125_17':ROOT.kBlack}

varnames = {
	'pt0' : 'p_{T}^{jet0}',
	'pt1' : 'p_{T}^{jet1}',
	'pt2' : 'p_{T}^{jet2}',
	'deltaEta' : '|#Delta#eta|',
	'deltaPhi' : '|#Delta#phi|',
	'deltaY' : '|#Delta y|'
}

histgroups = {}
for sample in samples.keys():
    inFile = ROOT.TFile.Open('rootfiles/XHYbbWWstudies_{}.root'.format(sample))
    histgroups[sample] = HistGroup(sample)
    for varname in varnames.keys():
	inhist = inFile.Get(varname)
	inhist.SetDirectory(0)
	histgroups[sample].Add(varname,inhist)
	print('Added {} distribution for sample {}'.format(varname, sample))

    inFile.Close()

print(histgroups.keys())

for varname in varnames.keys():
    bkg, sig = OrderedDict([('QCD',None), ('ttbar', None)]), OrderedDict([('MX1800-MY125_17',None)])
    bkg['QCD'] = histgroups['QCD'][varname]
    bkg['ttbar'] = histgroups['ttbar'][varname]
    sig['MX1800-MY125_17'] = histgroups['MX1800-MY125_17'][varname]

    CompareShapes(
	outfilename = 'plots/kinDist_{}.png'.format(varname),
	year = 'Run2',
	prettyvarname = varnames[varname],
	bkgs = bkg,
	signals = sig,
	colors = colors,
	names = samples,
	logy = False,
	doSoverB = True,
	stackBkg = True
    )
