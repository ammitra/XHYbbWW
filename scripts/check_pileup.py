import subprocess
eosls = 'eos root://cmseos.fnal.gov ls'
eosdir = '/store/user/ammitra/XHYbbWW/pileup/'

raw = subprocess.check_output('ls raw_nano/ | grep -v Data | grep -v JetsHT | grep -v ttbar | grep -v NMSSM | grep -v MX | grep -v backup | grep -v QCD | grep -v py | grep -v PFnano',shell=True).split('\n')
raw = [i.split('.txt')[0] for i in raw if 'txt' in i]

eos = subprocess.check_output('{} {} | grep -v Data | grep -v JetsHT | grep -v ttbar | grep -v NMSSM | grep -v MX | grep -v backup | grep -v QCD | grep -v py | grep -v PFnano'.format(eosls,eosdir),shell=True).split('\n')
eos = [i.split('XHYbbWWpileup_')[-1].split('.root')[0] for i in eos if 'root' in i]

missing_from_eos = list(set(raw)^set(eos))

print('Missing pileup files on EOS for:')
print(',\n\t'.join(missing_from_eos))
with open('pileup_jobs_to_rerun.txt','w') as f:
    for missing in missing_from_eos:
	setname = missing.split('_')[0]
	year = missing.split('_')[-1]
	arg = ' -s {} -y {}\n'.format(setname, year)
	f.write(arg)

