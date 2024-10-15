import glob

out = open('condor/studies_args.txt','w')
for f in glob.glob('trijet_nano/*.txt'):
    filename = f.split('/')[-1].split('.')[0]
    setname = filename.split('_')[0]
    year = filename.split('_')[1]
    # don't run studies on data
    if 'Data' in setname:
        continue

    out.write('-s {} -y {} -v None\n'.format(setname, year))
