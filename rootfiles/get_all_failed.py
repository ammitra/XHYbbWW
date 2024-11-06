'''
Gathers all rootfiles that failed the combined selection from the EOS (selection_redo/) and sends a hadded version to the normal selection directory (selection/)
'''
from glob import glob
import subprocess, os
from TIMBER.Tools.Common import ExecuteCmd
import ROOT

proc_systs = {
    'QCDHT1500_16': [''],
    'QCDHT700_16': [''],
    'QCDHT700_16APV': [''],
    'WJetsHT600_16': ['','JER','JES','JMR','JMS'],
    'WJetsHT600_17': ['','JER','JES','JMR','JMS'],
    'WJetsHT800_16APV': ['','JER','JES','JMR','JMS'],
    'ttbar-allhad_17':['','JER','JES','JMR','JMS'],
    'ttbar-semilep_16':['','JER','JES','JMR','JMS'],
    'ttbar-semilep_16APV':['','JER','JES','JMR','JMS']
}

def CombineCommonSets(setname_year, variation):
    source_dir = '/store/user/ammitra/XHYbbWW/selection_redo'
    target_dir = 'root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/selection'
    baseStr = f'XHYbbWWselection_{setname_year}{"_"+variation if variation != "" else ""}'
    # hadd won't do wildcards for the sources (at least for remote xrootd files), so workaround is here:
    if variation == '':
        filesToGet = f'xrdfsls -u {source_dir} | grep {baseStr} | grep -v up | grep -v down'
    else:
        filesToGet = f'xrdfsls -u {source_dir} | grep {baseStr}_'
    haddcmd = f'hadd -f -k {target_dir}/{baseStr}.root $({filesToGet})'
    ExecuteCmd(haddcmd,dryrun=False)

if __name__ == "__main__":
    for setname_year, variations in proc_systs.items():
        for variation in variations:
            if variation == '':
                print('--------------------------------------------------------------')
                print(f'Hadding files for {setname_year}, nominal')
                print('--------------------------------------------------------------')
                CombineCommonSets(setname_year,variation)
            else:
                for ud in ['up','down']:
                    var = f'{variation}_{ud}'
                    print('--------------------------------------------------------------')
                    print(f'Hadding files for {setname_year}, {var}')
                    print('--------------------------------------------------------------')
                    CombineCommonSets(setname_year,var)
                continue
