'''
Cutflow information is stored differently in snapshots and selection files. 
Snapshots: stored in Events TTree
	NPROC, NFLAGS, NJETS, NPT, NKIN
Selection: stored in Histogram
	nTop_CR, nTop_SR
	higgsF_{}, higgsL_{}, higgsP_{}
'''
import ROOT
import glob, os
from argparse import ArgumentParser
from collections import OrderedDict
import numpy as np
from decimal import Decimal

def generateCutflow(setName, selection=False):
    '''
	main function to generate the cutflow from snapshot and/or selection for a set
	setName   [str]  = set name as seen in snapshot/selection files
	selection [bool] = False if only snapshot, True if both
    '''
    if selection:
	snapVars = OrderedDict([('NPROC',0.),('NJETS',0.),('NPT',0.),('NETA',0.),('NMSD',0.),('nWTag_CR',0.),('higgsF_CR',0.),('higgsL_CR',0.),('higgsP_CR',0.),('nWTag_SR',0.),('higgsF_SR',0.),('higgsL_SR',0.),('higgsP_SR',0.)])
    else:
	snapVars = OrderedDict([('NPROC',0.),('NJETS',0.),('NPT',0.),('NETA',0.),('NMSD',0.)])

    years = OrderedDict([('16',snapVars.copy()), ('16APV', snapVars.copy()), ('17', snapVars.copy()), ('18', snapVars.copy())])

    # do snapshots
    for year, varDict in years.items():
	#if not os.path.exists('trijet_nano/{}_{}_snapshot.txt'.format(setName,year)):
	    #pass
	if ('MX' in setName) and (year != '17'): continue
	fileList = glob.glob('trijet_nano/{}*_{}_snapshot.txt'.format(setName,year))
        for snapFile in fileList:
       	    # need to get names of ROOT files from txt
	    fList = open(snapFile)
	    rFiles = [i.strip() for i in fList if i != '']
	    for fName in rFiles:
	        #print('opening {}'.format(fName))
	        f = ROOT.TFile.Open(fName, 'READ')
	        # check for empty TTrees
	        if not f.Get('Events'):
		    #print('Skipping file due to no Events TTree:\n\t{}'.format(fName))
		    continue
	        e = f.Get('Events')
	        if not e.GetEntry():
		    #print('Skipping file due to empty Events TTree:\n\t{}'.format(fName))
		    continue
		e.GetEntry()	# initialize all branches
	        for cut, num in varDict.items():
		    if ('SR' in cut) or ('CR' in cut):
		        pass		    
		    else:
			#print('Getting Leaf {}'.format(cut))
			if e.GetLeaf(cut):
	                    varDict[cut] += e.GetLeaf(cut).GetValue(0)
	        f.Close()

    if selection:
        # selection will have common sets joined by default (see rootfiles/get_all.py and perform_selection.py)
        # i.e.: 	THselection_ZJets_18.root
        for year, varDict in years.items():
	    if ('MX' in setName) and (year != '17'): continue
	    if not os.path.exists('rootfiles/XHYbbWWselection_HT0_{}_{}.root'.format(setName, year)):
	        pass
	    f = ROOT.TFile.Open('rootfiles/XHYbbWWselection_HT0_{}_{}.root'.format(setName, year))
	    h = f.Get('cutflow')
	    for i in range(1, 9):	# cutflow has 8 bins w the cuts, starting from index 1
	        var = h.GetXaxis().GetBinLabel(i)
	        val = h.GetBinContent(i)
	        varDict[var] += val
	    f.Close()

    # returns dict of {year: cutflowDict}
    return years


def printYields(selection=False):
    '''prints the yields for bkg and data in Latex form'''
    labels = ["Sample","nProc","nJets","p_{t}","#eta","m_{SD}"]
    if selection:
	labels.extend(["CR_WCut","CR_F","CR_L","CR_P","SR_WCut","SR_F","SR_L","SR_P"])
    sets = ["ttbar", "QCD", "Data"]

    for s in sets:
        res = generateCutflow(s, selection)
        print('\n------------------ {} -------------------'.format(s))
        for year, dicts in res.items():
	    print('----------------- {} -----------------'.format('20'+year))
	    latexRow = s + " &"
	    for var, val in dicts.items():
	        if (val > 10000):
		    latexRow += " {0:1.2e} &".format(val)
	        else:
		    latexRow += " {0:.3f} &".format(val)
            print(" & ".join(labels)+" \\\\")
            print(latexRow)

	'''
	#print(res)
        # just a short routine to check the impact of tight jetId cuts
	for year in ['16','16APV','17','18']:
            nJetID = float(res[year]['NJETID'])
            nJets = float(res[year]['NJETS'])
            print('20{} Percent loss from nJets -> nJetId cut: {}%'.format(year, (1.0 - nJetID/nJets)*100.))    
	'''

def printEfficiencies(selection=False):
    '''prints the efficiencies for various XHY samples.
	First, for mX = 1800, mY = 60, 125, 250, 350, 500
	Then, for mY = 125, mX = 600, 800, 1000, 1200, 1800, 2400, 3000  (SKIP 1700 - it's missing 2018)
    '''
    labels = ["Sample","nProc","nJets","p_{t}","#eta","nSoftDrop"]
    if selection:
	labels.extend(["CR_WCut","CR_F","CR_L","CR_P","SR_WCut","SR_F","SR_L","SR_P"])
    # first keep constant mT
    prefix = 'MX'
    mT = 2600
    phiMasses = [60, 125, 250, 350, 500, 600, 700, 800, 900, 1000, 1200, 1400, 1600]
    for mPhi in phiMasses:
	nProc = 0
	res = generateCutflow('{}{}-MY{}'.format(prefix, mT, mPhi), selection)
	print('\n------------------ {} -------------------'.format('{}{}-MY{}'.format(prefix, mT, mPhi)))
	for year, dicts in res.items():
	    if year != '17': continue
	    print('----------------- {} -----------------'.format('20'+year))
	    latexRow = '{}{}-MY{}'.format(prefix, mT, mPhi) + " &"
	    for var, val in dicts.items():
		if (var == 'NPROC'):
		    nProc = val
		    latexRow += " 1 &"
		else:
		    #latexRow += " {0:.3f} &".format(float(val)/float(nProc))
		    if (float(val)/float(nProc)) < 0.01:
			latexRow += ' %.2E &'%Decimal(float(val)/float(nProc))
		    else:
			latexRow += " {0:.3f} &".format(float(val)/float(nProc))
	    print(" & ".join(labels)+" \\\\")
	    print(latexRow)

    # now keep constant mPhi
    mPhi = 1800
    Tmasses = [600,800,1000,1200,1400,1600,1800,2000,2200,2400,2600,2800,3000]
    for Tmass in Tmasses:
	if (Tmass <= mPhi): continue
	nProc = 0
	res = generateCutflow('{}{}-MY{}'.format(prefix, Tmass, mPhi), selection)
	print('\n------------------ {} -------------------'.format('{}{}-MY{}'.format(prefix, Tmass, mPhi)))
	for year, dicts in res.items():
	    if year != '17': continue
	    print('----------------- {} -----------------'.format('20'+year))
	    latexRow = '{}{}-MY{}'.format(prefix, Tmass, mPhi) + " &"
	    for var, val in dicts.items():
                if (var == 'NPROC'):
                    nProc = val
                    latexRow += " 1 &"
                else:
                    #latexRow += " {0:.3f} &".format(float(val)/float(nProc))
		    if (float(val)/float(nProc)) < 0.01:
			latexRow += ' %.2E &'%Decimal(float(val)/float(nProc))
		    else:
			latexRow += " {0:.3f} &".format(float(val)/float(nProc))
            print(" & ".join(labels)+" \\\\")
            print(latexRow)

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--selection', action='store_true',
			help='Get cutflow/yield info for selection too. Do not include if you only want snapshot info.')
    
    args = parser.parse_args()

    #printYields(args.selection)
    printEfficiencies(args.selection)
