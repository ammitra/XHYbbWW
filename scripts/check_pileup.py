import subprocess, os
import ROOT
eosls = 'eos root://cmseos.fnal.gov ls'
eosdir = '/store/user/ammitra/XHYbbWW/pileup/'
xrdfsls='xrdfs root://cmseos.fnal.gov ls'

#raw = subprocess.check_output('ls raw_nano/ | grep -v Data | grep -v JetsHT | grep -v ttbar | grep -v NMSSM | grep -v MX | grep -v backup | grep -v QCD | grep -v py | grep -v PFnano',shell=True).split('\n')
raw = subprocess.check_output('ls raw_nano/ | grep .txt | grep -v Data | grep -v MX',shell=True).split('\n')
raw = [i for i in raw if os.path.getsize('raw_nano/%s'%i)] # check for empty raw nano files
raw = [i.split('.txt')[0] for i in raw if 'txt' in i]

#eos = subprocess.check_output('{} {} | grep -v Data | grep -v JetsHT | grep -v ttbar | grep -v NMSSM | grep -v MX | grep -v backup | grep -v QCD | grep -v py | grep -v PFnano'.format(eosls,eosdir),shell=True).split('\n')
eos = subprocess.check_output('{} {} | grep .root | grep -v Data | grep -v backup | grep -v MX'.format(eosls,eosdir),shell=True).split('\n')
eos = [i.split('XHYbbWWpileup_')[-1].split('.root')[0] for i in eos if 'root' in i]

missing_from_eos = list(set(raw)^set(eos))

# Now check which pileup files on EOS are missing the histograms
to_check = subprocess.check_output('{} -u {} | grep .root | grep -v Data | grep -v backup'.format(xrdfsls,eosdir),shell=True).split('\n')
to_check = [i for i in to_check if i != '']
empty_files = []
for i in to_check:
    setname_year = i.split('/')[-1].split('.')[0].split('_')[1:]
    histname = '_'.join(setname_year)
    if 'MX' in histname: continue #old version of signal files
    if not os.path.getsize('raw_nano/%s.txt'%histname):
        #print('PU file {} on EOS corresponds to empty file in raw_nano/ - skipping'.format(histname))
        continue
    fPU = ROOT.TFile.Open(i)
    if not (fPU.GetListOfKeys().Contains(histname)):
	print('PU file on EOS missing for dataset {}'.format(histname))
	arg = ' -s {} -y {}\n'.format(setname_year[0], setname_year[1])
	empty_files.append(arg)
    fPU.Close()

with open('pileup_jobs_to_rerun.txt','w') as f:
    for missing in missing_from_eos:
	setname = missing.split('_')[0]
	year = missing.split('_')[-1]
	if not os.path.getsize('raw_nano/%s_%s.txt'%(setname,year)):
	    print('skipping empty file: {}'.format(setname+'_'+year))
	    continue
	arg = ' -s {} -y {}\n'.format(setname, year)
	f.write(arg)
    for empty in empty_files:
	f.write(empty)

