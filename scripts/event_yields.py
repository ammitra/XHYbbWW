'''
Script to analyze the total number of events in the SR and CR for all of the processes.
Yields are calculated for different cases:
    1: no cuts or mass requirement
    2: W mass window requirement
    3: H mass cut
    4. W mass window req + H mass cut
'''
import ROOT
ROOT.gROOT.SetBatch(True)


redirector    = 'root://cmseos.fnal.gov/'
eos_path      = '/store/user/ammitra/XHYbbWW/selection_backup_14March2024_before_msd4Vec_mregCuts_50GeVregCut/'
base_hist_str = 'MXvMY_softdrop_particleNet_{mW}{region}{mH}__nominal'
base_file_str = 'XHYbbWWselection_HT0_{proc}_{year}.root'

processes = [
    'Data',
    'NMSSM-XHY-1800-800',
    #'ttbar-allhad','ttbar-semilep',
    #'WJetsHT400','WJetsHT600','WJetsHT600',
    #'ZJetsHT400','ZJetsHT600','ZJetsHT800',
    'WJets','ZJets','ttbar', 'QCD',
    'WW', 'WZ', 'ZZ',
    'ggZH-HToBB-ZToQQ','GluGluHToBB','GluGluHToWW-Pt-200ToInf-M-125',
    'ST-antitop4f','ST-top4f','ST-tW-antitop5f','ST-tW-top5f',
    'ttHToBB','ttHToNonbb-M125',
    'WminusH-HToBB-WToQQ','WplusH-HToBB-WToQQ','ZH-HToBB-ZToQQ',
    'HWminusJ-HToWW-M-125','HWplusJ-HToWW-M-125','HZJ-HToWW-M-125'
]

regions = ['SR_loose','SR_pass']#['CR_loose','CR_pass','SR_loose','SR_pass']

temp_dict = {proc:{region:-1 for region in regions} for proc in processes}
yield_dict = {i:temp_dict.copy() for i in range(1,5)}

out = open('EventYields.txt','w')

for region in regions:
    for proc in processes:
        if proc == 'Data': continue
        yield_lines = []
        print('Checking %s in region %s...'%(proc,region))
        for case in range(1,5):
            print('\tCase %s'%case)
            total = 0
            for year in ['16','16APV','17','18']:
                if case == 1:
                    hist_str = base_hist_str.format(mW='',region=region,mH='')
                elif case == 2:
                    hist_str = base_hist_str.format(mW='mWreg_cut_',region=region,mH='')
                elif case == 3:
                    hist_str = base_hist_str.format(mW='',region=region,mH='_mHreg_cut')
                else:
                    hist_str = base_hist_str.format(mW='mWreg_cut_',region=region,mH='_mHreg_cut')

                if ((case == 2) or (case == 4)) and ('CR' in region): continue
                f = ROOT.TFile.Open('%s%s%s'%(redirector,eos_path,base_file_str.format(proc=proc,year=year)),'READ')
                h = f.Get(hist_str)
                y = h.Integral()
                total += round(y)
                f.Close()

            yield_lines.append(total)
            yield_dict[case][proc][region] = total

        print(yield_lines)
        line = '| %s | %s | %s | %s | %s |\n'%(proc,yield_lines[0],yield_lines[1],yield_lines[2],yield_lines[3])
        out.write(line)
        print(line)

yield_lines = []
for region in regions:
    print('Checking data in region %s...'%(region))
    for case in range(1,5):
        if case == 1:
            hist_str = base_hist_str.format(mW='',region=region,mH='')
        elif case == 2:
            hist_str = base_hist_str.format(mW='mWreg_cut_',region=region,mH='')
        elif case == 3:
            hist_str = base_hist_str.format(mW='',region=region,mH='_mHreg_cut')
        else:
            hist_str = base_hist_str.format(mW='mWreg_cut_',region=region,mH='_mHreg_cut')
        if ((case == 2) or (case == 4)) and ('CR' in region): continue
        f = ROOT.TFile.Open('%s%sXHYbbWWselection_HT0_Data_Run2.root'%(redirector,eos_path),'READ')
        h = f.Get(hist_str)
        y = h.Integral()
        print(y)
        yield_lines.append(y)
        yield_dict[case]['Data'][region] = y

print(yield_lines)
line = '| %s | %s | %s | %s | %s |\n'%('Data',yield_lines[0],yield_lines[1],yield_lines[2],yield_lines[3])
out.write(line)
print(line)

out.close()

for i in range(1,5):
    print('------------------------- Case %s -------------------------'%(i))
    for region in regions:
        print('\tREGION: %s ---------------------------'%(region))
        for proc in processes:
            tot = yield_dict[i][proc][region]
            print('\t\t%s: %s'%(proc,tot))
    print('\n')
