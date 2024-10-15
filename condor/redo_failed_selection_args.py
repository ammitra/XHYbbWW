import glob
import subprocess

command = "eosls -l /store/user/ammitra/XHYbbWW/selection | awk '{if ($5 < 1000) print $9}'"

f = subprocess.check_output(command, shell=True)
files = [fname for fname in f.decode('utf-8').split('\n')]

out = open('condor/redo_failed_selection_args.txt','w') 
# syntax is:
# XHYbbWWselection_SETNAME_YEAR.root            - nominal
# XHYbbWWselection_SETNAME_YEAR_VAR_u/d.root    - variation
for fname in files:
    if fname == '': continue
    setname = fname.split('_')[1]
    year = fname.split('_')[2].split('.root')[0]
    var = 'None' if ('up' not in fname and 'down' not in fname) else fname.split('_')[3]
    ud = 'None' if ('up' not in fname and 'down' not in fname) else fname.split('_')[4].split('.root')[0]
    # find how many snapshots there are
    nfiles = len(open(f'trijet_nano/{setname}_{year}_snapshot.txt').readlines())
    variation = 'None' if var == 'None' else f'{var}_{ud}'
    for j in range(1,nfiles+1):
        out.write(f'-s {setname} -y {year} -v {variation} -j {j} -n {nfiles}\n')
out.close()

'''
# make the args for one variation per job
out = open('condor/selection_args.txt','w')
for f in glob.glob('raw_nano/*.txt'):
    if 'NOTES' in f: continue
    if 'Muon' in f: continue
    filename = f.split('/')[-1].split('.')[0]
    setname = filename.split('_')[0]
    year = filename.split('_')[1]

    if 'Data' not in setname and 'QCD' not in setname:
        out.write('-s {} -y {} -v None\n'.format(setname, year))
        systs = ['JES','JER','JMS','JMR']
        for syst in systs:
            for v in ['up','down']:
                out.write('-s {} -y {} -v {}_{}\n'.format(setname, year, syst, v))
    else:
        out.write('-s {} -y {} -v None\n'.format(setname, year))

out.close()
'''
