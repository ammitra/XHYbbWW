import ROOT
import glob
from array import array
import numpy as np
import matplotlib
import matplotlib as mpl
import matplotlib.pyplot as plt
from collections import OrderedDict
'''
Generates 2D plots (m_phi vs m_tphi) of the final signal efficiencies.
'''

mPhi = OrderedDict([(i,None) for i in [60,100,125,150,190,250,300,350,400,450,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2200,2400]])

def GetEfficiencies(year):
    '''year (str): 16, 16APV, 17, 18'''
    # Create the TPrime mass dict, with each TPrime mass point having a copy of the mPhi dict
    # There are no signal samples for T' = [2100,2200,2300,2500,2600,2700]
    efficiencies = OrderedDict([(i,mPhi.copy()) for i in range(600,3200,200)])
    # Loop through the selections and get the values
    for selection in glob.glob('rootfiles/XHYbbWWselection_HT0_*_{}.root'.format(year)):
	if 'MX' not in selection: continue
	TMass = int(selection.split('/')[-1].split('_')[2].split('-')[0].split('MX')[1])
	PhiMass = int(selection.split('/')[-1].split('_')[2].split('-')[1].split('MY')[1])
	f = ROOT.TFile.Open(selection,'READ')
	h = f.Get('cutflow')
	# want bins SR_WCut and SR_P, which are bins 5 and 8 (indexed from 1)
	start = h.GetBinContent(5)
	end   = h.GetBinContent(8)
	eff = end/start
	efficiencies[TMass][PhiMass] = eff


    # The Tprime masses (rows) are ['800', '900', '1000', '1100', '1200', '1300', '1400', '1500', '1600', '1700', '1800', '1900', '2000', '2400', '2800', '2900', '3000'] - 17 Tprime mass points
    effArr = np.zeros((13,23),dtype=float)
    #row = 13
    row = 0
    for TMass, PhiMasses in efficiencies.items():
	col = 22
	for PhiMass, eff in PhiMasses.items():
	    if col < 0: continue
	    if eff==None: eff = 0.0
	    effArr[row][col] = eff
            print('row: {}\ncol: {}\neff: {}\nMX: {}\nMY: {}\n'.format(row,col,eff,TMass,PhiMass))
	    col -= 1	    
        row += 1
    print(effArr)
    
    fig, ax = plt.subplots(figsize=(10,10))
    im = ax.imshow(100.*effArr.T)
    TMasses = [str(i) for i in range(600,3200,200)]
    #TMasses.reverse()
    PhiMasses = [str(i) for i in [60,100,125,150,190,250,300,350,400,450,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2200,2400]]
    PhiMasses.reverse()
    '''
    ax.set_xticks(np.arange(len(PhiMasses)))
    ax.set_xticklabels(PhiMasses)
    ax.set_yticks(np.arange(len(TMasses)))
    ax.set_yticklabels(TMasses)
    '''
    ax.set_xticks(np.arange(len(TMasses)))
    ax.set_xticklabels(TMasses)
    ax.set_yticks(np.arange(len(PhiMasses)))
    ax.set_yticklabels(PhiMasses)

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    for i in range(len(TMasses)):
	for j in range(len(PhiMasses)):
	    text = ax.text(i, j, '{}%'.format(round(effArr[i, j]*100.,1)),ha="center", va="center", color="w", fontsize='small')
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel('Signal Efficiency (%)', rotation=-90, va="bottom",fontsize='large')
    ax.set_title("Selection Signal Efficiency 20{}".format(year))
    ax.set_aspect('auto')
    plt.xlabel(r"$m_{X}$ [GeV]",fontsize='large')
    plt.ylabel(r"$m_{Y}$ [GeV]",fontsize='large')
    plt.savefig('plots/SignalEfficiencySelection_{}.png'.format(year),dpi=300)


if __name__=='__main__':
    for year in ['17']:
	GetEfficiencies(year)
	    
