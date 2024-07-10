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

def _addFile(TChain, f):
    '''Add file to TChains being tracked.
    Args:
        f (str): File to add.
    '''
    if f.endswith(".root"): 
        if 'root://' not in f and f.startswith('/store/'):
            f='root://cms-xrd-global.cern.ch/'+f
        if ROOT.TFile.Open(f,'READ') == None:
            raise ReferenceError('File %s does not exist'%f)
        tempF = ROOT.TFile.Open(f,'READ')
        if tempF.Get('Events') != None:
            TChain.Add(f)
        tempF.Close()
    elif f.endswith(".txt"): 
        txt_file = open(f,"r")
        for l in txt_file.readlines():
	    print('ROOT file: {}'.format(l))
            thisfile = l.strip()
            _addFile(TChain, thisfile)
    else:
        raise Exception("File name extension not supported. Please provide a single or list of .root files or a .txt file with a line-separated list of .root files to chain together.")
    

mPhi = OrderedDict([(i,None) for i in [60,70,80,90,100,125,150,190,250,300,350,400,450,500,600,700,800,900,1000,1100,1200,1300,1400,1600,1800,2000,2200,2400,2500,2600,2800]])

def GetEfficiencies(year):
    '''year (str): 16, 16APV, 17, 18'''
    efficiencies = OrderedDict([(i,mPhi.copy()) for i in [240,280,300,320,360,400,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2200,2400,2500,2600,2800,3000,3500,4000]])
    # Get the actual snapshots for a given year
    snapshots = glob.glob('trijet_nano/NMSSM*_{}_snapshot.txt'.format(year))
    # Loop through the snapshots and create a TChain for each
    for snapshot in snapshots:
	print('Opening: {}'.format(snapshot))
	TMass = int(snapshot.split('/')[-1].split('_')[0].split('-')[2])
	PhiMass = int(snapshot.split('/')[-1].split('_')[0].split('-')[3]
	TChain = ROOT.TChain('Events')
	_addFile(TChain, snapshot)
	# put everything in memory
	TChain.GetEntry()
	start = TChain.GetLeaf('NPROC').GetValue(0)
	end = TChain.GetLeaf('NMSD').GetValue(0)
	eff = end/start
	efficiencies[TMass][PhiMass] = eff
	print(start,end,eff)
    effArr = np.zeros((13,31),dtype=float)
    #row = 13
    row = 0
    for TMass, PhiMasses in efficiencies.items():
	col = 30
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
    ax.set_title("Snapshot Signal Efficiency 20{}".format(year))
    ax.set_aspect('auto')
    plt.xlabel(r"$m_{X}$ [GeV]",fontsize='large')
    plt.ylabel(r"$m_{Y}$ [GeV]",fontsize='large')
    plt.savefig('plots/SignalEfficiencySnapshot_{}.png'.format(year),dpi=300)


if __name__=='__main__':
    for year in ['17']:
	GetEfficiencies(year)
	    
