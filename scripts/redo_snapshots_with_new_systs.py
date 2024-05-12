'''
script to check which snapshot jobs are missing the updated systematics 
(5/2/24)
    -   ISRunc__up/down
    -   FSRunc__up/down
    -   QCDscale_uncert__down/up
'''
import subprocess
import ROOT

eosls   = 'eos root://cmseos.fnal.gov ls'
eosdir  = '/store/user/ammitra/XHYbbWW/snapshots/'
xrdfsls = 'xrdfs root://cmseos.fnal.gov ls'

snapshots = subprocess.check_output('%s -u %s | grep snapshot'%(xrdfsls, eosdir),shell=True,text=True).split('\n')

out = open('snapshots_redo_with_new_systs.txt','w')
for snap in snapshots:
    if 'ttbar' not in snap: continue
    f = ROOT.TFile.Open(snap,'READ')
    e = f.Get('Events')
    if e == None:
        print('%s has no events Tree'%snap)
        fname   = snap.split('HWWsnapshot_')[-1].split('.root')[0]
        setname = fname.split('_')[0]
        year    = fname.split('_')[1]
        njobs   = fname.split('_')[2].split('of')[-1]
        ijob    = fname.split('_')[2].split('of')[0]
        print('%s %s job %s/%s needs to be rerun'%(setname,year,ijob,njobs))
        out.write('-s %s -y %s -n %s -j %s\n'%(setname,year,njobs,ijob))
        continue
    if e.GetEntry() == 0:
        print('%s has an empty events tree'%snap)
        continue
    if 'Data' in snap: continue
    good = False
    for branch in e.GetListOfBranches():
        if branch.GetName() == "ISRunc__up": 
            good = True
    if good:
        continue
    else:
        fname   = snap.split('HWWsnapshot_')[-1].split('.root')[0]
        setname = fname.split('_')[0]
        year    = fname.split('_')[1]
        njobs   = fname.split('_')[2].split('of')[-1]
        ijob    = fname.split('_')[2].split('of')[0]
        print('%s %s job %s/%s needs to be rerun'%(setname,year,ijob,njobs))
        out.write('-s %s -y %s -n %s -j %s\n'%(setname,year,njobs,ijob))

