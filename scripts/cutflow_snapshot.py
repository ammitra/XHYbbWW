'''
Script to produce latex cutflow efficiency summaries for signal snapshots.
We will show the efficiency relative to the previous cut.
'''
import ROOT
import glob, os
from argparse import ArgumentParser
from collections import OrderedDict
import numpy as np
from decimal import Decimal

def generateCutflow(setName, y, selection=False):
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
        if year != y: continue
        if not os.path.exists('trijet_nano/{}_{}_snapshot.txt'.format(setName,year)):
            print(f'WARNING: file trijet_nano/{setName}_{year}_snapshot.txt does not exist')
            return None
        fileList = glob.glob('trijet_nano/{}_{}_snapshot.txt'.format(setName,year))
        for snapFile in fileList:
            # need to get names of ROOT files from txt
            fList = open(snapFile)
            rFiles = [i.strip() for i in fList if i != '']
            for fName in rFiles:
                #print('opening {} for {}'.format(fName,setName))
                f = ROOT.TFile.Open(fName, 'READ')
                # check for empty TTrees
                if not f.Get('Events'):
                    #print('Skipping file due to no Events TTree:\n\t{}'.format(fName))
                    return None
                e = f.Get('Events')
                if not e.GetEntry():
                    #print('Skipping file due to empty Events TTree:\n\t{}'.format(fName))
                    return None
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


base_top = r'''
\begin{table}[htbp!]
    \centering
    \begin{tabular}{ccccccc}
        \hline
        Sample & Start & nJets & \pt & \eta & \mSD & Overall \\
        \hline
'''

base_bottom = r'''
    \end{tabular}
    \caption{Snapshot efficiency for \mx = %s for all kinematically allowed \my, 20%s MC}
    \label{tab:cutflow_snapshot_mx%s_%s}
\end{table}
'''

def EfficiencyRow(mX, y):
    '''
    Gets the snapshot efficiency for a given mX with all possible mY. 
    '''
    labels = ["Signal", "Start", "nJets", r"\pt", r"\eta", r"\mSD"]
    mYs = [60,70,80,90,100,125,150,190,250,300,350,400,450,500,600,700,800,900,1000,1100,1200,1300,1400,1600,1800,2000,2200,2400,2500,2600,2800]
    print(f'\n------------------ 20{y} ------------------')

    fOut = open(f'latex/snapshot_efficiency_{mX}_{y}.txt','w')
    #fOut.write(r'Sample & Start & nJets & \pt & \eta & \mSD & Overall \\' + '\n')
    fOut.write(base_top)
    print(base_top)

    for mY in mYs:
        print(f'Doing mY = {mY}')
        last_val = 0    # store the last cutflow so we can calculate efficiencies relative to it 
        #START = 0
        #END = 0
        res = generateCutflow(f'NMSSM-XHY-{mX}-{mY}',y=y)
        if not res: 
            continue
        for year, dicts in res.items():
            START = 0
            END = 0
            if year != y: continue
            latexRow = '\t'
            latexRow += f'({mX},{mY})' + " &"
            for var, val in dicts.items():
                if (var=='NPROC'):
                    last_val = val
                    START = val
                if (var=='NMSD'):
                    END = val

                eff = float(val)/float(last_val)
                if eff < 0.01:
                    latexRow += ' %.2E &'%(Decimal(eff))
                elif eff == 1.0:
                    latexRow += ' 1.0 &'
                else:
                    latexRow += " {0:.3f} &".format(eff)

                # store the last value
                last_val = val
            
            # get the overall snapshot efficiency
            overall_eff = float(END)/float(START)
            latexRow += " {0:.1f}".format(overall_eff*100.) + r'\% \\' + '\n'

            print(latexRow)
            fOut.write(latexRow)

    fOut.write(
        base_bottom%(mX, y, mX, y)
    )
    print(base_bottom%(mX, y, mX, y))

    fOut.close()


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--selection', action='store_true',
                        help='Get cutflow/yield info for selection too. Do not include if you only want snapshot info.')

    
    args = parser.parse_args()

    '''
    for y in ['16','16APV','17','18']:
        for mx in [240,280,300,320,360,400,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2200,2400,2500,2600,2800,3000,3500,4000]:
            EfficiencyRow(mX=mx, y=y)
    '''
    EfficiencyRow(mX=4000,y='17')
