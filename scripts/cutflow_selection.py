'''
Script to produce latex cutflow efficiency summaries for signal selections.
We will show the efficiency relative to the previous cut.
'''
import ROOT
import glob, os
from argparse import ArgumentParser
from collections import OrderedDict
import numpy as np
from decimal import Decimal

def generateCutflow(setName, y):
    snapVars = OrderedDict([
        ('n_start',0.),('n_after_corrections',0.),('n_after_Has2Ws',0.),('n_after_WmassCut',0.),('n_after_SR_HbbMassCut',0.),('n_after_SR_pass_HbbScoreCut',0.)
    ])

    years = OrderedDict([('16',snapVars.copy()), ('16APV', snapVars.copy()), ('17', snapVars.copy()), ('18', snapVars.copy())])

    for year, varDict in years.items():
        if year != y: continue
        f_loc = f'root://cmseos.fnal.gov///store/user/ammitra/XHYbbWW/selection/XHYbbWWselection_{setName}_{year}.root'
        try:
            f = ROOT.TFile.Open(f_loc,'READ')

        except:
            print(f'EOS file for {setName} does not exist, skipping...')
            return None

        h = f.Get('cutflow')
        for i in range(1,11): # cutflow has 10 bins, starting from index 1
            if (i >= 5 and i <= 7) or (i==9): # these are VR cutflows and SR fail
                continue
            else:
                var = h.GetXaxis().GetBinLabel(i)
                val = h.GetBinContent(i)
                varDict[var] += val
        f.Close()

    # returns dict of {year: cutflowDict}
    return years


base_top = r'''
\begin{table}[htbp!]
    \centering
    \begin{tabular}{cccccccc}
        \hline
        Sample & Start & nCorr & n2Ws & nWMass & nHbbMass & & nXbbPass & Overall \\
        \hline
'''

base_bottom = r'''
    \end{tabular}
    \caption{Final selection efficiency for \mx = %s for all kinematically allowed \my, relative to the preselection efficiency, for 20%s MC}
    \label{tab:cutflow_snapshot_mx%s_%s}
\end{table}
'''

def EfficiencyRow(mX, y):
    mYs = [60,70,80,90,100,125,150,190,250,300,350,400,450,500,600,700,800,900,1000,1100,1200,1300,1400,1600,1800,2000,2200,2400,2500,2600,2800]
    print(f'\n------------------ 20{y} ------------------')

    fOut = open(f'latex/selection_efficiency_{mX}_{y}.txt','w')
    fOut.write(base_top)
    print(base_top)

    for mY in mYs:
        print(f'Doing mY = {mY}')
        last_val = 0    # store the last cutflow so we can calculate efficiencies 
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
                if (var=='n_start'):
                    last_val = val
                    START = val
                if (var=='n_after_SR_pass_HbbScoreCut'):
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
    EfficiencyRow(mX=1800,y='17')
