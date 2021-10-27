import glob

out = open('condor/pileup_args.txt','w')
for f in glob.glob('raw_nano/*.txt'):
    # filename format is "setname_year.txt" or "XYH_WWbb_MX_XMASS_MY_YMASSloc.txt"
    filename = f.split('/')[-1].split('.')[0]
    # determine if file is signal or not
    if 'XYH_WWbb' in filename:
        name = filename.split('_')
        # need to put the setname into something that the class can parse
        setname = (name[2] + '_' + name[3] + '_' + name[4] + '_' + name[5])     # MX_XMASS_MY_YMASS
        year = '18'     # might have to change later
    elif 'Data' in filename:
	continue
    else:
        setname = filename.split('_')[0]
        year = filename.split('_')[1]
    # now write to file
    out.write('-s {} -y {}\n'.format(setname, year))

out.close()
