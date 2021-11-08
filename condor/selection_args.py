import glob

out = open('condor/selection_args.txt','w')
for f in glob.glob('raw_nano/*.txt'):
    # filename format is "setname_year.txt" or "XYH_WWbb_MX_XMASS_MY_YMASSloc.txt"
    filename = f.split('/')[-1].split('.')[0]
    if 'XYH_WWbb' in filename:
	name = filename.split('_')
	# need to put the setname into something that the class can parse
	setname = (name[2] + '_' + name[3] + '_' + name[4] + '_' + name[5])	# MX_XMASS_MY_YMASS 
	year = '18'	# might have to change later
    else:
	setname = filename.split('_')[0]
	year = filename.split('_')[1]

    if 'Data' in setname:
	out.write('-s {} -y {}\n'.format(setname, year))

    else:
	# we don't have to worry about these corrections for QCD, since it's just for validation. 
	if ('QCD' in setname):
	    out.write('-s {} -y {}\n'.format(setname, year))
	else:
            # now create the variations 
            for var in ['JES','JMS','JER','JMR']:
	        for ud in ['up','down']:
	            v = var + '_' + ud
	            out.write('-s {} -y {} -v {}\n'.format(setname, year, v))
	    out.write('-s {} -y {}\n'.format(setname, year))

out.close()
