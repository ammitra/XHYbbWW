from glob import glob
import subprocess, os
from TIMBER.Tools.Common import ExecuteCmd

redirector = 'root://cmseos.fnal.gov/'
eos_path = '/store/user/{}/XHYbbWW/snapshots/'.format(os.getenv('USER'))

# gather the names of the snapshot ROOT files
print("Running eos {} ls {}".format(redirector, eos_path))
files = subprocess.check_output('eos {} ls {}'.format(redirector, eos_path), shell=True)

print(files)

org_files = {}
for f in files.split('\n'):
    if (f == '') or ('pileup' in f):
	# not sure why XHYbbWWpileup.root ends up in snapshots/ dir, but just skip it 
	continue

    # file format: HWWsnapshot_SETNAME_YEAR_XofY.root
    info = f.split('.')[0].split('_')	# get everything before .root, make list split on '_'

    setname = info[1]
    year = info[2]
   
    file_path = redirector + eos_path + f

    # org_files = { year : { setname : [filepaths]
    if year not in org_files.keys():	# create new key of this year
	org_files[year] = {}
    if setname not in org_files[year].keys():
	org_files[year][setname] = []
        
    org_files[year][setname].append(file_path)

# again, we have here org_files = { year : { setname : filepath
for y in org_files.keys():
    for s in org_files[y].keys():
	out = open('trijet_nano/{}_{}_snapshot.txt'.format(s, y), 'w')  # setname_era_snapshot.txt
	for f in org_files[y][s]: 
	    out.write(f+'\n')  # write a new line after each
	out.close()

# consolidate data files (i.e. one file for each setname + year)
# just leave this commented for now, not too important
'''
subdatafiles = glob('trijet_nano/Data*_{}_snapshot.txt'.format(y))
ExecuteCmd('rm trijet_nano/Data_{0}_snapshot.txt'.format(y))
ExecuteCmd('cat trijet_nano/Data*_{0}_snapshot.txt > trijet_nano/Data_{0}_snapshot.txt'.format(y))
for s in subdatafiles:
    if s != 'trijet_nano/Data_{0}_snapshot.txt'.format(y):
        ExecuteCmd('rm {}'.format(s))
'''
