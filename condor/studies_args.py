import glob

out = open('condor/studies_args.txt','w')
for f in glob.glob('trijet_nano/*.txt'):
    # filename format is "setname_year_snapshot.txt" or "MX_XMASS_MY_YMASS_snapshot.txt"
    filename = f.split('/')[-1].split('.')[0]
    if 'MX' in filename:
	name = filename.split('_')
	# need to put the setname into something that the class can parse
	setname = (name[0] + '_' + name[1] + '_' + name[2] + '_' + name[3])	# MX_XMASS_MY_YMASS 
	year = '18'	# might have to change later
    else:
	setname = filename.split('_')[0]
	year = filename.split('_')[1]

    # don't run studies on data
    if 'Data' in setname:
	continue

    out.write('-s {} -y {}\n'.format(setname, year))
