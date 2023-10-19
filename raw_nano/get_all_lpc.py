from TIMBER.Tools.Common import ExecuteCmd
import sys
das = {
    "16": {
	"NMSSM_XHY": "/NMSSM_XToYHTo2W2BTo4Q2B_MX-XMASS_MY-YMASS_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL16NanoAODv9-106X_mcRun2_asymptotic_v17-v1/NANOAODSIM",
        "ttbar-allhad": "/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODv9-106X_mcRun2_asymptotic_v17-v1/NANOAODSIM",
        "ttbar-semilep": "/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODv9-106X_mcRun2_asymptotic_v17-v1/NANOAODSIM",
        "QCDHT700": "/QCD_HT700to1000_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIISummer20UL16NanoAODv9-106X_mcRun2_asymptotic_v17-v1/NANOAODSIM",
        "QCDHT1000": "/QCD_HT1000to1500_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIISummer20UL16NanoAODv9-106X_mcRun2_asymptotic_v17-v1/NANOAODSIM",
        "QCDHT1500": "/QCD_HT1500to2000_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIISummer20UL16NanoAODv9-106X_mcRun2_asymptotic_v17-v1/NANOAODSIM",
        "QCDHT2000": "/QCD_HT2000toInf_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIISummer20UL16NanoAODv9-106X_mcRun2_asymptotic_v17-v1/NANOAODSIM",
        "DataF":  "/JetHT/Run2016F-UL2016_MiniAODv2_NanoAODv9-v1/NANOAOD",
        "DataG":  "/JetHT/Run2016G-UL2016_MiniAODv2_NanoAODv9-v1/NANOAOD",
        "DataH":  "/JetHT/Run2016H-UL2016_MiniAODv2_NanoAODv9-v1/NANOAOD",
        "SingleMuonDataF": "/SingleMuon/Run2016F-UL2016_MiniAODv2_NanoAODv9-v1/NANOAOD",
        "SingleMuonDataG": "/SingleMuon/Run2016G-UL2016_MiniAODv2_NanoAODv9-v1/NANOAOD",
        "SingleMuonDataH": "/SingleMuon/Run2016H-UL2016_MiniAODv2_NanoAODv9-v1/NANOAOD"
    },
    "16APV": {
	"NMSSM_XHY": "/NMSSM_XToYHTo2W2BTo4Q2B_MX-XMASS_MY-YMASS_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL16NanoAODAPVv9-106X_mcRun2_asymptotic_preVFP_v11-v1/NANOAODSIM",
        "ttbar-allhad": "/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODAPVv9-106X_mcRun2_asymptotic_preVFP_v11-v1/NANOAODSIM",
        "ttbar-semilep": "/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODAPVv9-106X_mcRun2_asymptotic_preVFP_v11-v1/NANOAODSIM",
        "QCDHT700": "/QCD_HT700to1000_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIISummer20UL16NanoAODAPVv9-106X_mcRun2_asymptotic_preVFP_v11-v1/NANOAODSIM",
        "QCDHT1000": "/QCD_HT1000to1500_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIISummer20UL16NanoAODAPVv9-106X_mcRun2_asymptotic_preVFP_v11-v1/NANOAODSIM",
        "QCDHT1500": "/QCD_HT1500to2000_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIISummer20UL16NanoAODAPVv9-106X_mcRun2_asymptotic_preVFP_v11-v1/NANOAODSIM",
        "QCDHT2000": "/QCD_HT2000toInf_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIISummer20UL16NanoAODAPVv9-106X_mcRun2_asymptotic_preVFP_v11-v1/NANOAODSIM",
        "DataB":  "/JetHT/Run2016B-ver2_HIPM_UL2016_MiniAODv2_NanoAODv9-v2/NANOAOD",
        "DataC":  "/JetHT/Run2016C-HIPM_UL2016_MiniAODv2_NanoAODv9-v2/NANOAOD",
        "DataD":  "/JetHT/Run2016D-HIPM_UL2016_MiniAODv2_NanoAODv9-v2/NANOAOD",
        "DataE":  "/JetHT/Run2016E-HIPM_UL2016_MiniAODv2_NanoAODv9-v2/NANOAOD",
        "DataF":  "/JetHT/Run2016F-HIPM_UL2016_MiniAODv2_NanoAODv9-v2/NANOAOD",
        "SingleMuonDataB": "/SingleMuon/Run2016B-ver2_HIPM_UL2016_MiniAODv2_NanoAODv9-v2/NANOAOD",
        "SingleMuonDataC": "/SingleMuon/Run2016C-HIPM_UL2016_MiniAODv2_NanoAODv9-v2/NANOAOD",
        "SingleMuonDataD": "/SingleMuon/Run2016D-HIPM_UL2016_MiniAODv2_NanoAODv9-v2/NANOAOD",
        "SingleMuonDataE": "/SingleMuon/Run2016E-HIPM_UL2016_MiniAODv2_NanoAODv9-v2/NANOAOD",
        "SingleMuonDataF": "/SingleMuon/Run2016F-HIPM_UL2016_MiniAODv2_NanoAODv9-v2/NANOAOD"
    },
    "17": {
	"NMSSM_XHY": "/NMSSM_XToYHTo2W2BTo4Q2B_MX-XMASS_MY-YMASS_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
        "ttbar-allhad": "/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
        "ttbar-semilep": "/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
        "QCDHT700": "/QCD_HT700to1000_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
        "QCDHT1000": "/QCD_HT1000to1500_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
        "QCDHT1500": "/QCD_HT1500to2000_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
        "QCDHT2000": "/QCD_HT2000toInf_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
        "DataB": "/JetHT/Run2017B-UL2017_MiniAODv2_NanoAODv9-v1/NANOAOD",
        "DataC": "/JetHT/Run2017C-UL2017_MiniAODv2_NanoAODv9-v1/NANOAOD",
        "DataD": "/JetHT/Run2017D-UL2017_MiniAODv2_NanoAODv9-v1/NANOAOD",
        "DataE": "/JetHT/Run2017E-UL2017_MiniAODv2_NanoAODv9-v1/NANOAOD",
        "DataF": "/JetHT/Run2017F-UL2017_MiniAODv2_NanoAODv9-v1/NANOAOD",
        "SingleMuonDataB": "/SingleMuon/Run2017B-UL2017_MiniAODv2_NanoAODv9-v1/NANOAOD",
        "SingleMuonDataC": "/SingleMuon/Run2017C-UL2017_MiniAODv2_NanoAODv9-v1/NANOAOD",
        "SingleMuonDataD": "/SingleMuon/Run2017D-UL2017_MiniAODv2_NanoAODv9-v1/NANOAOD",
        "SingleMuonDataE": "/SingleMuon/Run2017E-UL2017_MiniAODv2_NanoAODv9-v1/NANOAOD",
        "SingleMuonDataF": "/SingleMuon/Run2017E-UL2017_MiniAODv2_NanoAODv9-v1/NANOAOD"
    },
    "18": {
	"NMSSM_XHY": "/NMSSM_XToYHTo2W2BTo4Q2B_MX-XMASS_MY-YMASS_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
        "ttbar-allhad": "/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
        "ttbar-semilep": "/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
        "QCDHT700": "/QCD_HT700to1000_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v2/NANOAODSIM",
        "QCDHT1000": "/QCD_HT1000to1500_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
        "QCDHT1500": "/QCD_HT1500to2000_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
        "QCDHT2000": "/QCD_HT2000toInf_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
        "DataA": "/JetHT/Run2018A-UL2018_MiniAODv2_NanoAODv9-v2/NANOAOD",
        "DataB": "/JetHT/Run2018B-UL2018_MiniAODv2_NanoAODv9-v1/NANOAOD",
        "DataC": "/JetHT/Run2018C-UL2018_MiniAODv2_NanoAODv9-v1/NANOAOD",
        "DataD": "/JetHT/Run2018D-UL2018_MiniAODv2_NanoAODv9-v2/NANOAOD",
        "SingleMuonDataA": "/SingleMuon/Run2018A-UL2018_MiniAODv2_NanoAODv9_GT36-v1/NANOAOD",
        "SingleMuonDataB": "/SingleMuon/Run2018B-UL2018_MiniAODv2_NanoAODv9_GT36-v1/NANOAOD",
        "SingleMuonDataC": "/SingleMuon/Run2018C-UL2018_MiniAODv2_NanoAODv9_GT36-v1/NANOAOD",
        "SingleMuonDataD": "/SingleMuon/Run2018D-UL2018_MiniAODv2_NanoAODv9_GT36-v1/NANOAOD"
    }
}

def GetFiles(das_name,setname,year):
    ExecuteCmd('dasgoclient -query "file dataset=%s" > %s_%s_temp.txt'%(das_name,setname,year),'dryrun' in sys.argv)
    f = open('%s_%s_temp.txt'%(setname,year),'r')
    fout = open('raw_nano/%s_%s.txt'%(setname,year),'w')
    for l in f.readlines():
        fout.write('root://cmsxrootd.fnal.gov/'+l)
    f.close()
    fout.close()
    if 'dryrun' not in sys.argv:
        ExecuteCmd('rm %s_%s_temp.txt'%(setname,year),'dryrun' in sys.argv)

latex_lines = {"16":[],"16APV":[],"17":[],"18":[]}
for year in das.keys():
    for setname in das[year].keys():
	if 'XHY' in setname:
	    for mX in [240,280,300,320,360,400,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2200,2400,2500,2600,2800,3000,3500,4000]:
		for mY in [60,70,80,90,100,125,150,190,250,300,350,400,450,500,600,700,800,900,1000,1100,1200,1300,1400,1600,1800,2000,2200,2400,2500,2600,2800]:
		    if mY+125>mX:
			print('\tMY({}) + MH(125) = {} > MX({})'.format(mY,mY+125,mX))
			continue
		    das_name = das[year][setname].replace('XMASS',str(mX)).replace('YMASS',str(mY))
		    setname_mod = '{}-{}-{}'.format(setname,mX,mY)
		    GetFiles(das_name, setname_mod, year)
		    latex_lines[year].append('| {} | {} |'.format(setname_mod.replace('-',' ')+' GeV', das_name))
	else:
            GetFiles(das[year][setname],setname,year)
            latex_lines[year].append('| %s | %s |'%(setname,das[year][setname]))
            
for y in sorted(latex_lines.keys()):
    print ('\n20%s'%y)
    print ('| Setname | DAS location |')
    print ('|---------|--------------|')
    for l in latex_lines[y]: print (l)
