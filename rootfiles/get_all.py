'''
Gathers all rootfiles from the EOS and dumps it into the rootfiles/ directory 
'''
from glob import glob
import subprocess, os
from TIMBER.Tools.Common import ExecuteCmd
import ROOT

def GetAllFiles():
    return [f for f in glob('dijet_nano/*_snapshot.txt') if f != '']
def GetProcYearFromTxt(filename):
    pieces = filename.split('/')[-1].split('.')[0].split('_')
    if '.txt' in filename:
        return pieces[0], pieces[1]
    elif '.root' in filename:
        return pieces[1], pieces[2]
    else:
        print('ERROR')

def CombineCommonSets(groupname,doStudies=False,modstr='',HT='',remote=False):
    '''Which stitch together either QCD or ttbar (ttbar-allhad+ttbar-semilep)
    @param groupname (str, optional): QCD/ttbar/W/Z/ST.
    '''
    
    for y in ['16','16APV','17','18']:
        if not remote:
            baseStr = 'rootfiles/XHYbbWW%s_{0}{2}_{1}{3}.root'%('studies' if doStudies else 'selection')
        else:
            baseStr = 'root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/selection/XHYbbWW%s_{0}{2}_{1}{3}.root'%('studies' if doStudies else 'selection')
        if groupname == 'TT':
            to_loop = [''] if doStudies else ['','JES','JER','JMS','JMR']
            for v in to_loop:
                if v == '':
                    ExecuteCmd('hadd -f -k %s %s %s'%(
                        baseStr.format('ttbar',y,modstr,''),
                        baseStr.format('ttbar-allhad',y,modstr,''),
                        baseStr.format('ttbar-semilep',y,modstr,''))
                    )
                else:
                    for v2 in ['up','down']:
                        v3 = '_%s_%s'%(v,v2)
                        ExecuteCmd('hadd -f -k %s %s %s'%(
                            baseStr.format('ttbar',y,modstr,v3),
                            baseStr.format('ttbar-allhad',y,modstr,v3),
                            baseStr.format('ttbar-semilep',y,modstr,v3))
                        )
        elif groupname == 'QCD':
            ExecuteCmd('hadd -f -k %s %s %s %s %s'%(
                baseStr.format('QCD',y,modstr,''),
                baseStr.format('QCDHT700',y,modstr,''),
                baseStr.format('QCDHT1000',y,modstr,''),
                baseStr.format('QCDHT1500',y,modstr,''),
                baseStr.format('QCDHT2000',y,modstr,''))
            )

        elif groupname == 'ST':
            to_loop = [''] if doStudies else ['','JES','JER','JMS','JMR']
            for v in to_loop:
                if v == '':
                    ExecuteCmd('hadd -f -k %s %s %s %s %s'%(
                        baseStr.format('ST',y,modstr,''),
                        baseStr.format('ST-antitop4f',y,modstr,''),
                        baseStr.format('ST-top4f',y,modstr,''),
                        baseStr.format('ST-tW-antitop5f',y,modstr,''),
                        baseStr.format('ST-tW-top5f',y,modstr,''))
                    )
                else:
                    for v2 in ['up','down']:
                        v3 = '_%s_%s'%(v,v2)
                        ExecuteCmd('hadd -f -k %s %s %s %s %s'%(
                            baseStr.format('ST',y,modstr,v3),
                            baseStr.format('ST-antitop4f',y,modstr,v3),
                            baseStr.format('ST-top4f',y,modstr,v3),
                            baseStr.format('ST-tW-antitop5f',y,modstr,v3),
                            baseStr.format('ST-tW-antitop5f',y,modstr,v3))
                        )

        elif groupname == 'W' or 'Z':
            to_loop = [''] if doStudies else ['','JES','JER','JMS','JMR']
            for v in to_loop:
                if v == '':
                    ExecuteCmd('hadd -f -k %s %s %s %s'%(
                        baseStr.format('{}Jets'.format('W' if groupname == 'W' else 'Z'),y,modstr,''),
                        baseStr.format('{}JetsHT400'.format('W' if groupname == 'W' else 'Z'),y,modstr,''),
                        baseStr.format('{}JetsHT600'.format('W' if groupname == 'W' else 'Z'),y,modstr,''),
                        baseStr.format('{}JetsHT800'.format('W' if groupname == 'W' else 'Z'),y,modstr,''))
                    )
                else:
                    for v2 in ['up','down']:
                        v3 = '_{}_{}'.format(v,v2)
                        ExecuteCmd('hadd -f -k %s %s %s %s'%(
                            baseStr.format('{}Jets'.format('W' if groupname == 'W' else 'Z'),y,modstr,v3),
                            baseStr.format('{}JetsHT400'.format('W' if groupname == 'W' else 'Z'),y,modstr,v3),
                            baseStr.format('{}JetsHT600'.format('W' if groupname == 'W' else 'Z'),y,modstr,v3),
                            baseStr.format('{}JetsHT800'.format('W' if groupname == 'W' else 'Z'),y,modstr,v3))
                        )

def MakeRun2(source_path):
    target = 'root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/selection/XHYbbWWselection_Data_Run2.root'
    sources = f'xrdfsls -u {source_path} | grep Data | grep -v Run2'
    haddcmd = f'hadd -f -k {target} $({sources})'
    ExecuteCmd(haddcmd,dryrun=False)


# ------------------------------------------------------------------------------------------
if __name__ == '__main__':
    redirector = 'root://cmseos.fnal.gov/'
    eos_path = '/store/user/ammitra/XHYbbWW/selection/'

    '''
    # combine common sets with different HT bins and/or decays, using the remote flag 
    CombineCommonSets('TT',doStudies=False,HT='',remote=True)
    CombineCommonSets('W',doStudies=False,HT='',remote=True)
    CombineCommonSets('Z',doStudies=False,HT='',remote=True)
    CombineCommonSets('QCD',doStudies=False,HT='',remote=True)
    CombineCommonSets('ST',doStudies=False,HT='',remote=True)
    '''
    # Combine all of the Run 2 data
    MakeRun2(eos_path) 
