'''
Script to remove empty (unfinished) selection files from EOS and produce an output 
file with all of the jobs to redo.
'''
import subprocess
from TIMBER.Tools.Common import ExecuteCmd
import ROOT

files = subprocess.check_output('xrdfs root://cmseos.fnal.gov ls -u /store/user/ammitra/XHYbbWW/selection/',shell=True,text=True).split('\n')

proc_year = {}

removed = 0
for f in files:
    temp = ROOT.TFile.Open(f)
    h = temp.Get('cutflow')
    if h == None:
        print('%s missing cutflow hist'%(temp))
        fname = f.split('cmseosmgm01.fnal.gov:1094/')[-1]
        procname = fname.split('/store/user/ammitra/XHYbbWW/selection/XHYbbWWselection_HT0_')[-1].split('.root')[0].split('_')[0]
        year = fname.split('/store/user/ammitra/XHYbbWW/selection/XHYbbWWselection_HT0_')[-1].split('.root')[0].split('_')[1]
        print('deleting %s, 20%s'%(procname,year))
        if procname in proc_year:
            if year in proc_year[procname]:
                continue
            else:
                proc_year[procname].append(year)
        else:
            proc_year[procname] = [year]
        ExecuteCmd('eos root://cmseos.fnal.gov rm %s'%fname)
        removed += 1
print('% files removed'%removed)

with open('selection_removed_jobs_to_rerun.txt','w') as f:
    for proc, years in proc_years.items():
        for year in years:
            f.write('-s %s -y %s --HT 0\n'%())

