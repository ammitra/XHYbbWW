'''
script to check which selection jobs are missing on the EOS, based on the snapshots 
that have been completed.
'''
import subprocess
import ROOT

eosls   = 'eos root://cmseos.fnal.gov ls'
eosdir  = '/store/user/ammitra/XHYbbWW/selection/'
xrdfsls = 'xrdfs root://cmseos.fnal.gov ls'
redirector = 'root://cmseos.fnal.gov'

def get_snapshots():
    '''gets all of the completed snapshots'''
    procs_snap = subprocess.check_output('ls trijet_nano/ | grep snapshot.txt', shell=True, text=True).split('\n')
    procs = [i.split('.txt')[0].split('_snapshot')[0] for i in procs_snap if 'txt' in i]
    return procs

def get_selection():
    '''gets all existing EOS selection files in a list'''
    eos_selection = subprocess.check_output('%s %s'%(eosls,eosdir),shell=True,text=True).split('\n')
    selection = [i for i in eos_selection if 'XHYbbWWselection' in i]
    return selection

def get_process(selection_list, procname):
    '''from the EOS selection list, isolate only the given process'''
    proc = procname.split('_')[0]
    year = procname.split('_')[-1]
    to_check = 'XHYbbWWselection_HT0_%s_%s_'%(proc,year)
    procs = [i for i in selection_list if to_check in i]
    return procs

def check_all_systs(proc, year, proc_list, syst_list):
    '''from the EOS selection list for a given process, check that all systs are made'''
    to_rerun = []
    if (len(syst_list) == len(proc_list)):
        return to_rerun
    else:
        for syst in syst_list:
            found = False
            for fname in proc_list:
                if syst == 'None':
                    if '%s_%s.root' in fname:
                        found = True
                else:
                    if syst in fname:
                        found = True
            if not found:
                print('syst %s not found in %s'%(syst,fname))
                out = '-s %s -y %s -v %s --HT 0\n'%(proc,year,syst) 
                to_rerun.append(out)
        return to_rerun

if __name__ == "__main__":
    eos_snapshots = get_snapshots() # get all existing snapshots
    eos_selection = get_selection() # get all existing selection files on EOS
    out = open('selection_jobs_to_rerun.txt','w')
    for process_year in eos_snapshots:  # loop over EOS snapshots, check if they exist
        proc = process_year.split('_')[0]
        year = process_year.split('_')[1]
        # get all files on EOS corresponding to proc_year
        eos_proc = get_process(eos_selection, process_year)
        # check if all systematics exist for this process
        systs = ['None'] # nominal, no systematic variation
        if ('ttbar' in proc) or ('NMSSM' in proc):
            systs.extend(['PNetHbb_up','PNetHbb_down','PNetWqq_up','PNetWqq_down','JES_up','JES_down','JER_up','JER_down','JMS_up','JMS_down','JMR_up','JMR_down'])
        elif ('Data' in proc) or ('QCD' in proc):
            pass
        else:
            systs.extend(['JES_up','JES_down','JER_up','JER_down','JMS_up','JMS_down','JMR_up','JMR_down'])
        to_rerun = check_all_systs(proc, year, eos_proc, systs)
        for job in to_rerun:
            out.write(job)
    out.close()
