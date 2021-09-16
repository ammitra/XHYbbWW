from argparse import Namespace
from glob import glob
from XHYbbWW_studies import XHYbbWW_studies
from TIMBER.Tools.Common import DictStructureCopy, CompileCpp, ExecuteCmd, OpenJSON, StitchQCD
from TIMBER.Tools.Plot import CompareShapes
from TIMBER.Analyzer import Correction
import ROOT

def GetAllFiles():
    return [f for f in glob('trijet_nano/*_snapshot.txt') if f != '']

def GetProcYearFromTxt(filename):
    '''
    DataA_18_snapshot.txt
    MX_1300_MY_200_18_snapshot.txt
    '''
    pieces = filename.split('/')[-1].split('.')[0].split('_')
    if 'MX' in filename:
        proc = "{}_{}_{}_{}".format(pieces[0],pieces[1],pieces[2],pieces[3])
        year = pieces[4]
    else:
        proc = pieces[0]
        year = pieces[1]
    return proc, year

def GetProcYearFromROOT(filename):
    '''
    XHYbbWWstudies_QCDHT2000_17.root
    XHYbbWWstudies_MX_2000_MY_400_18.root
    '''
    pieces = filename.split('/')[-1].split('.')[0].split('_')
    if 'MX' in filename:
        proc = "{}_{}_{}_{}".format(pieces[1],pieces[2],pieces[3],pieces[4])
        year = pieces[5]
    else:
        proc = pieces[1]
        year = pieces[2]
    return proc, year

def GetHistDict(histname, all_files):
    all_hists = {
        'bkg':{},'sig':{},'data':None
    }
    for f in all_files:
        proc, year = GetProcYearFromROOT(f)
        tfile = ROOT.TFile.Open(f)
        hist = tfile.Get(histname)
        if hist == None:
            raise ValueError('Histogram {} does not exist in {}.'.format(histname,f))
        hist.SetDirectory(0)
        if 'MX' in proc:
            all_hists['sig'][proc] = hist
        elif 'Data' in proc:
            all_hists['data'] = hist
        else:
            all_hists['bkg'][proc] = hist
    return all_hists

def CombineCommonSets(groupname, doStudies=True):
    '''
    Which stitch together either QCD or ttbar (ttbar-allhad+ttbar-semilep)
    @param groupname (str, optional): "QCD" or "ttbar".
    '''
    if groupname not in ["QCD","ttbar"]:
        raise ValueError('Can only combine QCD or ttbar')
    config = OpenJSON("XHYbbWWconfig.json")
    for y in ['16','17','18']:
        baseStr = 'rootfiles/XHYbbWW%s_{0}_{1}{2}.root'%('studies' if doStudies else 'selection')
        if groupname == 'ttbar':
            for v in ['']:
                if v == '':
                    ExecuteCmd('hadd -f %s %s %s'%(
                        baseStr.format('ttbar',y,''),
                        baseStr.format('ttbar-allhad',y,''),
                        baseStr.format('ttbar-semilep',y,''))
                    )
                else:
                    for v2 in ['up','down']:
                        v3 = '_%s_%s'%(v,v2)
                        ExecuteCmd('hadd -f %s %s %s'%(
                            baseStr.format('ttbar',y,v3),
                            baseStr.format('ttbar-allhad',y,v3),
                            baseStr.format('ttbar-semilep',y,v3))
                        )
        elif groupname == 'QCD':
            ExecuteCmd('hadd -f %s %s %s %s %s'%(
                baseStr.format('QCD',y,''),
                baseStr.format('QCDHT700',y,''),
                baseStr.format('QCDHT1000',y,''),
                baseStr.format('QCDHT1500',y,''),
                baseStr.format('QCDHT2000',y,''))
            )
    
    MakeRun2(groupname)

def MakeRun2(setname, doStudies=True):
    t = 'studies' if doStudies else 'selection'
    # hadd <ofile> <ifiles>
    ExecuteCmd('hadd -f rootfiles/XHYbbWW{1}_{0}_Run2.root rootfiles/XHYbbWW{1}_{0}_16.root rootfiles/XHYbbWW{1}_{0}_17.root rootfiles/XHYbbWW{1}_{0}_18.root'.format(setname,t))

def MakeRun2Signal(doStudies=True):
    t = 'studies' if doStudies else 'selection'
    sig = glob('rootfiles/XHYbbWWstudies_MX_*')   # get all signal study files
    for s in sig:
	if 'Run2' in s:
	    return    # we've already done the renaming/copying
	else:
	    name = s.split('/')[-1].split('.')[0].split('_')
	    setname = '{}_{}_{}_{}'.format(name[1],name[2],name[3],name[4])	               # just rename all the MX_MY signal files
            ExecuteCmd('cp rootfiles/XHYbbWW{1}_{0}_18.root rootfiles/XHYbbWW{1}_{0}_Run2.root'.format(setname, t))

def plot(histname, fancyname):
    files = [f for f in glob('rootfiles/XHYbbWWstudies_*_Run2.root')]
    hists = GetHistDict(histname,files)

    CompareShapes('plots/%s_Run2.pdf'%histname,1,fancyname,
                   bkgs=hists['bkg'],
                   signals=hists['sig'],
                   names={},
                   colors={'QCD':ROOT.kYellow,'ttbar':ROOT.kRed,'TprimeB-1200':ROOT.kBlack},
                   scale=False, stackBkg=True, 
                   doSoverB=True)

if __name__ == "__main__":
    CombineCommonSets('QCD',doStudies=True)     # True by default, but just to show it here
    CombineCommonSets('ttbar',doStudies=True)
    MakeRun2('QCD',doStudies=True)
    MakeRun2('ttbar',doStudies=True)
    MakeRun2Signal()

    histNames = {
        'pt0':'Higgs jet p_{T} (GeV)',
        'pt1':'Lead W jet p_{T} (GeV)',
        'pt2':'Sublead W jet p_{T} (GeV)',
        'HT':'Scalar sum trijet p_{T} (GeV)',
        'deltaEta':'|#Delta #eta|',
        'deltaPhi':'|#Delta #phi|',
        'deltaY':'|#Delta y|',
        'mH_particleNet':'Higgs jet mass (with ParticleNet tag)',
        'mW1_particleNet':'Lead W jet mass (with ParticleNet tag)',
        'mW2_particleNet':'Sublead W jet mass (with ParticleNet tag)',
	'H_particleNet':'ParticleNet Higgs tag score',
	'W1_particleNet':'ParticleNet lead W tag score',
	'W2_particleNet':'ParticleNet sublead W tag score'
    }
    tempfile = ROOT.TFile.Open('rootfiles/XHYbbWWstudies_MX_1300_MY_200_18.root','READ')
    allValidationHists = [k.GetName() for k in tempfile.GetListOfKeys() if 'Idx' not in k.GetName()]
    for h in allValidationHists:
	print('Plotting {}'.format(h))
	if h in histNames.keys():
	    plot(h,histNames[h])
	else:
	    plot(h,h)
