from argparse import Namespace
from glob import glob
from XHYbbWW_studies import XHYbbWW_studies
from TIMBER.Tools.Common import DictStructureCopy, CompileCpp, ExecuteCmd, OpenJSON, StitchQCD
from TIMBER.Tools.Plot import CompareShapes, EasyPlots
import ROOT

def GetAllFiles():
    return [f for f in glob('trijet_nano/*_snapshot.txt') if f != '']

def GetProcYearFromTxt(filename):
    ''' formats:
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
    ''' formats:
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
            raise ValueError('Histogram %s does not exist in %s.'%(histname,f))
        hist.SetDirectory(0)
        if 'MX' in proc:
            all_hists['sig'][proc] = hist
        elif proc == 'Data':
            all_hists['data'] = hist
        else:
            all_hists['bkg'][proc] = hist
    return all_hists

def CombineCommonSets(groupname, doStudies=True):
    '''
    First stitch together either QCD or ttbar (ttbar-allhad+ttbar-semilep):
        XHYbbWWstudies_QCD_{year}.root
        XHYbbWWstudies_ttbar_{year}.root
    Then uses MakeRun2() to combine all years. Final output:  
        XHYbbWWstudies_QCD_Run2.root
        XHYbbWWstudies_ttbar_Run2.root
    '''
    if groupname not in ["QCD","ttbar"]:
        raise ValueError('Can only combine QCD or ttbar')
    config = OpenJSON("XHYbbWWconfig.json")
    for y in ['16','17','18']:
        baseStr = 'rootfiles/XHYbbWW%s_{0}_{1}{2}.root'%('studies' if doStudies else 'selection')
        if groupname == 'ttbar':
            for v in ['']:
                if v == '':
                    # this will result in the 16,17,18 ttbar (semilep and hadronic) all being combined 
                    ExecuteCmd('hadd -f %s %s %s'%(
                        baseStr.format('ttbar',y,''),
                        baseStr.format('ttbar-allhad',y,''),
                        baseStr.format('ttbar-semilep',y,''))
                    )
                else:
                    # no need to worry about this just yet
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
    '''
    Gathers all bkg files from 16,17,18 and hadds them to:
        rootfiles/XHYbbWWstudies_{setname}_Run2.root
    '''
    t = 'studies' if doStudies else 'selection'
    # hadd <ofile> <ifiles>
    ExecuteCmd('hadd -f rootfiles/XHYbbWW{1}_{0}_Run2.root rootfiles/XHYbbWW{1}_{0}_16.root rootfiles/XHYbbWW{1}_{0}_17.root rootfiles/XHYbbWW{1}_{0}_18.root'.format(setname,t))

def MakeRun2Signal(doStudies=True):
    '''
    Since for now we're just arbirtarily attributing the signal to 2018 (so file format works w the other scripts), we just have to add Run2 to the names
    Will only run if the script hasn't been run before. Output:
        XHYbbWW_MX_XMASS_MY_YMASS_Run2.root
    '''
    t = 'studies' if doStudies else 'selection'
    sig = glob('rootfiles/XHYbbWWstudies_MX_*')   # get all signal study files
    for s in sig:
	name = s.split('/')[-1].split('.')[0].split('_')
	setname = '{}_{}_{}_{}'.format(name[1],name[2],name[3],name[4])	               # just rename all the MX_MY signal files
        ExecuteCmd('cp rootfiles/XHYbbWW{1}_{0}_18.root rootfiles/XHYbbWW{1}_{0}_Run2.root'.format(setname, t))

# maybe think about adding args later to only do CERTAIN mass points (MX, MY), for now just do all
def plot(histname, fancyname):
    # we want to plot mX vs mY for the three score regions for QCD, ttbar, and Signal    
    files = [f for f in glob('rootfiles/XHYbbWWstudies_*_Run2.root')]
    hists = GetHistDict(histname, files)
    # at this point, we know we are only plotting 2D hists for QCD, ttbar, or signal
    # use the built-in TIMBER plotting function to make life easy
    for SorB, histos in hists.items():        # histname : {'bkg':{'ttbar':HISTO,'QCD':HISTO}, 'sig':{'sig1':HISTO,'sig2':HISTO,...}}
	if SorB == 'data': continue
	for proc, histo in histos.items():    # 'ttbar':HISTO,'QCD':HISTO       'sig1':HISTO,'sig2':HISTO,...
	    #print('{} - {}'.format(proc,histo))
	    # output PDF name will be of the form Region{}_MXvsMY_QCD.pdf, etc
	    EasyPlots('plots/{}_{}.pdf'.format(histname,proc), [histo], xtitle='m_{X} (GeV)', ytitle='m_{Y} (GeV)')

	    # now do the same, but for Y-projection
	    twoDhists = [histo]
	    for h in twoDhists:
		p = h.ProjectionY()
		EasyPlots('plots/{}_ProjY_{}.pdf'.format(histname,proc), [p], xtitle='m_{Y} (GeV)')

if __name__ == "__main__":
    CombineCommonSets('QCD',doStudies=True)
    CombineCommonSets('ttbar',doStudies=True)
    MakeRun2('QCD',doStudies=True)
    MakeRun2('ttbar',doStudies=True)
    MakeRun2Signal()

    # the files will have a 2D plot called Region{}_MXvsMY - {1,2,3}
    # we are only plotting the mX vs mY, we can just ignore the rest of the histos in there
    hist_names = {
	'Region1_MXvsMY':'mX vs mY for HbbvsQCD < 0.8',
	'Region2_MXvsMY':'mX vs mY for 0.8 < HbbvsQCD < 0.98',
	'Region3_MXvsMY':'mX vs mY for HbbvsQCD > 0.98'
    }

    tempfile = ROOT.TFile.Open('rootfiles/XHYbbWWstudies_MX_1300_MY_200_18.root','READ')
    allValidationHists = [k.GetName() for k in tempfile.GetListOfKeys() if 'Idx' not in k.GetName()]
    print('Plotting mX vs mY')
    for h in allValidationHists:
	if h in hist_names.keys():
	    print('Plotting {}'.format(h))
	    plot(h,hist_names[h])
	else:
	    continue
    
