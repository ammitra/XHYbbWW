import glob

out = open('condor/selection_args.txt','w')
for f in glob.glob('raw_nano/*.txt'):
    # filename format is "setname_year.txt" or "XYH_WWbb_MX_XMASS_MY_YMASSloc.txt"
    filename = f.split('/')[-1].split('.')[0]
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
	    out.write('-s {} -y {} -v None\n'.format(setname, year))

out.close()
