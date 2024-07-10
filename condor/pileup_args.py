import glob, os

out = open('condor/pileup_args.txt','w')
for f in glob.glob('raw_nano/*.txt'):
    # filename format is "setname_year.txt" 
    filename = f.split('/')[-1].split('.')[0]
    if not os.path.getsize(f):
        print('file {} size zero - double check on CMS DAS'.format(filename))
        continue
    if 'Data' in filename:
	continue
    else:
        setname = filename.split('_')[0]
        year = filename.split('_')[1]
    # now write to file
    out.write('-s {} -y {} -j 1 -n 1\n'.format(setname, year))

out.close()

# the ones to redo 
jobs = open('pileup_jobs_to_rerun.txt','r')
to_rerun = [i.strip() for i in jobs.readlines() if i != '']
jobs.close()
out2 = open('condor/pileup_args_split.txt','w')
for job in to_rerun:
    print(job)
    setname = job.split(' ')[1]
    year = job.split(' ')[-1]
    rawname = 'raw_nano/%s_%s.txt'%(setname,year)
    print(rawname)
    nfiles = len(open(rawname,'r').readlines())
    njobs = int(nfiles/5)
    njobs = nfiles
    for i in range(1,njobs+1):
	out2.write('-s {} -y {} -j {} -n {}\n'.format(setname,year,i,njobs))
out2.close()
