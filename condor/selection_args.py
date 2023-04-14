import glob

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('--HT', type=str, dest='HT',
                    action='store', default='0',
                    help='Value of HT to cut on')
parser.add_argument('--recycle', dest='recycle',
                    action='store_true', default=False,
                    help='Recycle existing files and just plot.')
args = parser.parse_args()

out = open('condor/selection_args_HT{}.txt'.format(args.HT),'w')
for f in glob.glob('raw_nano/*.txt'):
    # filename format is "setname_year.txt" or "XYH_WWbb_MX_XMASS_MY_YMASSloc.txt"
    filename = f.split('/')[-1].split('.')[0]
    setname = filename.split('_')[0]
    year = filename.split('_')[1]

    if 'Data' not in setname and 'QCD' not in setname:
	out.write('-s {} -y {} -v None --HT {}\n'.format(setname, year, args.HT))
	systs = ['JES','JER','JMS','JMR']
	if 'MX' in setname:
	    systs.extend(['PNetHbb','PNetWqq'])
	for syst in systs:
	    for v in ['up','down']:
		out.write('-s {} -y {} -v {}_{} --HT {}\n'.format(setname, year, syst, v, args.HT))
    else:
	out.write('-s {} -y {} -v None --HT {}\n'.format(setname, year, args.HT))

out.close()
