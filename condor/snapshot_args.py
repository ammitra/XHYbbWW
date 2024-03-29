import glob, os

out = open('condor/snapshot_args.txt','w')
for f in glob.glob('raw_nano/*.txt'):
    # filename format is "setname_year.txt"
    filename = f.split('/')[-1].split('.')[0]
    if not os.path.getsize(f):
	print('file {} size zero - double check on CMS DAS'.format(filename))
	continue
    nfiles = len(open(f,'r').readlines())
    setname = filename.split('_')[0]
    year = filename.split('_')[1]

    # now write to file
    if 'NMSSM' in filename:
	# PFNano signals are generated with a ton of small files, so its ok just to split them up into fewer jobs
	# but official MC are generated w 1 or 2 files, better to just keep it to one job to limit number of condor jobs
	njobs = nfiles
    else:
        njobs = int(nfiles/2)
    if njobs == 0: 	# this occurs when nfiles = 1
	njobs += 1
    for i in range(1, njobs+1):
	out.write('-s {} -y {} -j {} -n {}\n'.format(setname, year, i, njobs))

out.close()
