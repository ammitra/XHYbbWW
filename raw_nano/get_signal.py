import ROOT
import glob
import subprocess
from TIMBER.Tools.Common import ExecuteCmd
import sys

'''
This script gets all of the privately-generated PFNano signal files
'''

redirector = 'root://cmsxrootd.fnal.gov/'
eosls = 'eos root://cmseos.fnal.gov ls'

signalDirs = {
    '2017': 'raw_nano/PFNano_signals_2017.txt',
}

# signal file format contains list of dirs looking like: 
# /store/user/lpcpfnano/cmantill/v2_3/2017/XHYPrivate/NMSSM_XToYH_MX1600_MY300_HTo2bYTo2W_hadronicDecay/NMSSM_XToYH_MX1600_MY300_HTo2bYTo2W_hadronicDecay/221013_211514/0000
for year, signalFile in signalDirs.items():
    f = open(signalFile, 'r')
    lines = f.readlines()
    for line in lines:
	line = line.split('\n')[0]
	process = line.split('/')[8]
	mX = process.split('_')[2]
	mY = process.split('_')[3]
	print('Opening file for ({},{}), {}'.format(mX,mY,year))
	sigName = '{}-{}'.format(mX,mY)
	fNames = subprocess.check_output(['{} {}'.format(eosls, line)],shell=True).split('\n')
	fNames.remove('')
	fNames.remove('log')
	oFile = open('raw_nano/{}_{}.txt'.format(sigName,year.split('20')[-1]),'w')
	for name in fNames:
	    oFile.write('{}{}/{}\n'.format(redirector,line,name))
	oFile.close()
