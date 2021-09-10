import glob

out = open('condor/snapshot_args.txt','w')
for f in glob.glob('raw_nano/*.txt'):
    # filename format is "setname_year.txt" or "XYH_WWbb_MX_<MASS>_loc.txt"
    filename = f.split('/')[-1].split('.')[0]
    nfiles = len(open(f,'r').readlines())
    # determine if file is signal or not
    if 'XYH_WWbb' in filename:
	setname = (filename.split('_')[2]) + '-' + (filename.split('_')[3])
	year = '18'	# might have to change later
    else:
	setname = filename.split('_')[0]
	year = filename.split('_')[1]

    # now write to file
    njobs = int(nfiles/2)
    for i in range(1, njobs+1):
	out.write('-s {} -y {} -j {} -n {}\n'.format(setname, year, i, njobs))

out.close()
