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
    out.write('-s {} -y {}\n'.format(setname, year))

out.close()
