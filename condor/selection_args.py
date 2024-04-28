import glob

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('--HT', type=str, dest='HT',
                    action='store', default='0',
                    help='Value of HT to cut on')
args = parser.parse_args()

# make the args for Condor jobs with all variations in one job
out_multi = open('condor/selection_args_HT{}_all_variations.txt'.format(args.HT),'w')
# make the args for one variation per job
out = open('condor/selection_args_HT{}.txt'.format(args.HT),'w')
for f in glob.glob('raw_nano/*.txt'):
    # filename format is "setname_year.txt" or "XYH_WWbb_MX_XMASS_MY_YMASSloc.txt"
    if 'NOTES' in f: continue
    filename = f.split('/')[-1].split('.')[0]
    setname = filename.split('_')[0]
    year = filename.split('_')[1]

    if 'Data' not in setname and 'QCD' not in setname:
        out.write('-s {} -y {} -v None --HT {}\n'.format(setname, year, args.HT))
        systs = ['JES','JER','JMS','JMR']
        if ('NMSSM' in setname) or ('ttbar' in setname):
            systs.extend(['PNetHbb','PNetWqq'])
        for syst in systs:
            for v in ['up','down']:
                out.write('-s {} -y {} -v {}_{} --HT {}\n'.format(setname, year, syst, v, args.HT))
    else:
        out.write('-s {} -y {} -v None --HT {}\n'.format(setname, year, args.HT))

    out_multi.write('-s %s -y %s --HT %s\n'%(setname, year, args.HT))

out.close()
out_multi.close()

