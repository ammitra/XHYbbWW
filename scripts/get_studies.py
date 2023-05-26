from TIMBER.Tools.Common import ExecuteCmd
import subprocess, os
from glob import glob

eosls='eos root://cmseos.fnal.gov ls'
eosdir='/store/user/ammitra/XHYbbWW/studies/'

files = subprocess.check_output('{} {}'.format(eosls,eosdir), shell=True)

for f in files.split('\n'):
    if (f==''): continue
    ExecuteCmd('xrdcp root://cmseos.fnal.gov/{}{} rootfiles/'.format(eosdir,f))
