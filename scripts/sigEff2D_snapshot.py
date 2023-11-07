import ROOT
import glob
from array import array
import numpy as np
import matplotlib
import matplotlib as mpl
import matplotlib.pyplot as plt
from collections import OrderedDict

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

# ordered dictionary of Y mass keys with (initially empty) efficiency values
mY = OrderedDict([(i,None) for i in [60,70,80,90,100,125,150,190,250,300,350,400,450,500,600,700,800,900,1000,1100,1200,1300,1400,1600,1800,2000,2200,2400,2500,2600,2800]])
#mY = OrderedDict([(i,None) for i in [125, 150, 300, 500]])

def GetEfficiencies(year):
    '''year (str): 16, 16APV, 17, 18'''
    # make an efficiency dict of {mX : {mY : eff}}
    efficiencies = OrderedDict([(i, mY.copy()) for i in [240,280,300,320,360,400,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2200,2400,2500,2600,2800,3000,3500,4000]])
    #efficiencies = OrderedDict([(i, mY.copy()) for i in [800, 1000, 1800, 2000, 3000, 4000]])
    # get the actual snapshots for a given year
    snapshots = glob.glob('trijet_nano/NMSSM*_{}_snapshot.txt'.format(year))
    for snapshot in snapshots:
	print('opening: {}'.format(snapshot))
	xmass = int(snapshot.split('/')[-1].split('_')[0].split('-')[2])
	ymass = int(snapshot.split('/')[-1].split('_')[0].split('-')[3])
	TChain = ROOT.TChain('Events')
	_addFile(TChain, snapshot)
	TChain.GetEntry()
	start = TChain.GetLeaf('NPROC').GetValue(0)
	end = TChain.GetLeaf('NMSD').GetValue(0)
	eff = end/start
	efficiencies[xmass][ymass] = eff

    effArr = np.zeros((25,31),dtype=float)
    #effArr = np.zeros((6,4),dtype=float)
    col = 0 # columns are fixed x mass
    for xmass, ymasses in efficiencies.items():
	row = len(ymasses)-1 # rows are fixed y mass
	for ymass, eff in ymasses.items():
	    if row < 0: continue
	    if eff == None: eff = 0.0
	    effArr[col][row] = eff
	    print('row: {}\ncol: {}\neff: {}\nMX: {}\nMY: {}\n'.format(row,col,eff,xmass,ymass))
	    row -= 1
	col += 1
    print(effArr)

    fig, ax = plt.subplots(figsize=(15,15))
    im = ax.imshow(100.*effArr.T)
    #xmasses = [str(i) for i in [800, 1000, 1800, 2000, 3000, 4000]]
    #ymasses = [str(i) for i in [125, 150, 300, 500]]
    xmasses = [str(i) for i in [240,280,300,320,360,400,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2200,2400,2500,2600,2800,3000,3500,4000]]
    ymasses = [str(i) for i in [60,70,80,90,100,125,150,190,250,300,350,400,450,500,600,700,800,900,1000,1100,1200,1300,1400,1600,1800,2000,2200,2400,2500,2600,2800]]
    ymasses.reverse()

    ax.set_xticks(np.arange(len(xmasses)))
    ax.set_xticklabels(xmasses)
    ax.set_yticks(np.arange(len(ymasses)))
    ax.set_yticklabels(ymasses)

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    for i in range(len(xmasses)):
	for j in range(len(ymasses)):
	    efficiency = round(effArr[i, j]*100.,1)
	    if efficiency == 0.0: continue
	    if efficiency < 50.:
		textcolor='white'
	    else:
		textcolor='grey'
	    text = ax.text(i, j, '{}%'.format(round(effArr[i, j]*100.,1)),ha="center", va="center", color=textcolor, fontsize='small', rotation=45, rotation_mode='anchor')
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel('Signal Efficiency (%)', rotation=-90, va="bottom",fontsize='large')
    ax.set_title("Snapshot Signal Efficiency 20{}".format(year))
    ax.set_aspect('auto')
    plt.xlabel(r"$m_{X}$ [GeV]",fontsize='large')
    plt.ylabel(r"$m_{Y}$ [GeV]",fontsize='large')
    plt.savefig('sigEff2D_snapshot_{}.png'.format(year),dpi=300)

if __name__ == "__main__":
    for year in ['16','16APV','17','18']:
	GetEfficiencies(year)

