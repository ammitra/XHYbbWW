import glob

out = open('condor/snapshot_args.txt','w')
for f in glob.glob('raw_nano/*.txt'):
    # filename format is "setname_year.txt"
    filename = f.split('/')[-1].split('.')[0]
    nfiles = len(open(f,'r').readlines())
    setname = filename.split('_')[0]
    year = filename.split('_')[1]

    # now write to file
    if 'MX' in filename:
	# signals are generated with a ton of small files, so its ok just to split them up into fewer jobs
	njobs = 2
    else:
        njobs = int(nfiles/2)
    if njobs == 0: 	# this occurs when nfiles = 1
	njobs += 1
    for i in range(1, njobs+1):
	out.write('-s {} -y {} -j {} -n {}\n'.format(setname, year, i, njobs))

out.close()
