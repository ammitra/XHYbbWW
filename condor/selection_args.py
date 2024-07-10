import glob

from argparse import ArgumentParser
parser = ArgumentParser()
args = parser.parse_args()

# make the args for one variation per job
out = open('condor/selection_args.txt','w')
for f in glob.glob('raw_nano/*.txt'):
    if 'NOTES' in f: continue
    if 'Muon' in f: continue
    filename = f.split('/')[-1].split('.')[0]
    setname = filename.split('_')[0]
    year = filename.split('_')[1]

    if 'Data' not in setname and 'QCD' not in setname:
        out.write('-s {} -y {} -v None\n'.format(setname, year))
        systs = ['JES','JER','JMS','JMR']
        for syst in systs:
            for v in ['up','down']:
                out.write('-s {} -y {} -v {}_{}\n'.format(setname, year, syst, v))
    else:
        out.write('-s {} -y {} -v None\n'.format(setname, year))

out.close()
