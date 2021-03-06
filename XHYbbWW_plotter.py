from argparse import Namespace
from glob import glob
from XHYbbWW_studies import XHYbbWW_studies
from TIMBER.Tools.Common import DictStructureCopy, CompileCpp, ExecuteCmd, OpenJSON, StitchQCD
from TIMBER.Tools.Plot import CompareShapes
from TIMBER.Analyzer import Correction
import ROOT
from collections import OrderedDict

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
    # we want to ensure that the signals stay in the proper order for the S/sqrt(B) significance pane, so we use an OrderedDict for the 'sig' key
    all_hists = {
        'bkg':{},'sig':OrderedDict([]),'data':None
    }
    # gather all signal histograms in a (proc,hist) tuple to form the OrderedDict
    sigHists = []
    for f in all_files:
        proc, year = GetProcYearFromROOT(f)
        tfile = ROOT.TFile.Open(f)
        hist = tfile.Get(histname)
        if hist == None:
            raise ValueError('Histogram {} does not exist in {}.'.format(histname,f))
        hist.SetDirectory(0)
        if 'MX' in proc:
            print('PROC = {}'.format(proc))
	    sigHists.append((proc,hist))    # OrderedDict requires (k,v)
        elif 'Data' in proc:
            all_hists['data'] = hist
        else:
            all_hists['bkg'][proc] = hist
    # we've finished all the data and bkg dicts, now lets do signal
    # first, find MX=2000, MY=800    
    MX2000MY800_element = 0
    for i in range(len(sigHists)):
	if ('MX_2000' in sigHists[i][0]) and ('MY_800' in sigHists[i][0]):
	    MX2000MY800_element = i
	    #print(sigHists[i][0])
    # now add that as the first element in all_hists['sig']
    all_hists['sig'][sigHists[MX2000MY800_element][0]] = sigHists[MX2000MY800_element][1]
    for i in range(len(sigHists)):
	if (i == MX2000MY800_element):
	    # we've already added (2000,800) as the first key in the OrderedDict
	    continue
	else:
	    # we need to add the rest of the signal processes to the OrderedDict
	    all_hists['sig'][sigHists[i][0]] = sigHists[i][1]    # equivalent to all_hists['sig'][proc] = hist
    # at this point, this should be good to go. 
    # This method just ensures that the "first" signal in the all_hists['sig'] dict belongs to a mass w relatively high signal, thus ensuring that the S/sqrt(B) pane chooses a signal which mostly passes selection (unlike a lower mass one - say MX=1300)
    #print(all_hists['sig'])
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
	if 'Run2' in s:
	    return    # we've already done the renaming/copying
	else:
	    name = s.split('/')[-1].split('.')[0].split('_')
	    setname = '{}_{}_{}_{}'.format(name[1],name[2],name[3],name[4])	               # just rename all the MX_MY signal files
            ExecuteCmd('cp rootfiles/XHYbbWW{1}_{0}_18.root rootfiles/XHYbbWW{1}_{0}_Run2.root'.format(setname, t))

def plot(histname, fancyname, scale=True):
    '''
    generates plots based on a dictionary of hist names and their LaTeX fancy name
    hist names are compared against an existing studies file (with N-1 info). If hist name DNE in histo, just use name in histo
    @param: scale=True by default, but passed as CL argument
    '''
    files = [f for f in glob('rootfiles/XHYbbWWstudies_*_Run2.root')]
    hists = GetHistDict(histname,files)

    # we want to ensure that the plots show the signals in the same order, so we used OrderedDict in the GetHistDict() function
    # so, when hists['sig'] is called, the first element should ALWAYS be the histograms from the MX_2000_MY_800 signal, and this is the signal whose S/sqrt(B) will be displayed 
    
    # we also want to remove the S/sqrt(B) significance pane for kinematic plots.
    if 'particleNet' not in histname:
	# we are plotting kinematics
        CompareShapes('plots/%s_Run2.pdf'%histname,1,fancyname,
                   bkgs=hists['bkg'],
                   signals=hists['sig'],
                   names={},
                   colors={'QCD':ROOT.kOrange,'ttbar':ROOT.kRed,'MX_1300_MY_200':ROOT.kBlack,'MX_1500_MY_400':ROOT.kGray,'MX_2000_MY_400':ROOT.kBlue,'MX_2000_MY_800':ROOT.kCyan,'MX_3000_MY_800':ROOT.kGreen},
                   scale=scale, stackBkg=True,
                   doSoverB=False) 

    elif ('H_cut' in histname) or ('W1_cut' in histname) or ('W2_cut' in histname):
	# we are plotting a tagger cut
	# plot with log scale
        CompareShapes('plots/%s_LOGSCALE_Run2.pdf'%histname,1,fancyname,
                   bkgs=hists['bkg'],
                   signals=hists['sig'],
                   names={},
                   colors={'QCD':ROOT.kOrange,'ttbar':ROOT.kRed,'MX_1300_MY_200':ROOT.kBlack,'MX_1500_MY_400':ROOT.kGray,'MX_2000_MY_400':ROOT.kBlue,'MX_2000_MY_800':ROOT.kCyan,'MX_3000_MY_800':ROOT.kGreen},
                   scale=scale, stackBkg=True,
                   doSoverB=True,
		   logy=True)
	# plot without log scale (just so we can compare all N-1 and see which looks better)
        CompareShapes('plots/%s_Run2.pdf'%histname,1,fancyname,
                   bkgs=hists['bkg'],
                   signals=hists['sig'],
                   names={},
                   colors={'QCD':ROOT.kOrange,'ttbar':ROOT.kRed,'MX_1300_MY_200':ROOT.kBlack,'MX_1500_MY_400':ROOT.kGray,'MX_2000_MY_400':ROOT.kBlue,'MX_2000_MY_800':ROOT.kCyan,'MX_3000_MY_800':ROOT.kGreen},
                   scale=scale, stackBkg=True,
                   doSoverB=True)

    elif ('SR' in histname) or ('CR' in histname):
	# this will be handled in XHYbbWW_MXvsMY_plotter.py, just pass for now
	pass

    else:
	# we are plotting N-1 or something else, show significance
        CompareShapes('plots/%s_Run2.pdf'%histname,1,fancyname,
                   bkgs=hists['bkg'],
                   signals=hists['sig'],
                   names={},
                   colors={'QCD':ROOT.kOrange,'ttbar':ROOT.kRed,'MX_1300_MY_200':ROOT.kBlack,'MX_1500_MY_400':ROOT.kGray,'MX_2000_MY_400':ROOT.kBlue,'MX_2000_MY_800':ROOT.kCyan,'MX_3000_MY_800':ROOT.kGreen},
                   scale=scale, stackBkg=True, 
                   doSoverB=True)

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()

    # only arg we need for now is the hist scaling (normalization)
    parser.add_argument('--scale', dest='scale',
                        action='store_true', default=True,
                        help='scale histograms to unity')
    parser.add_argument('--noscale', dest='scale',
                        action='store_false', default=False,
                        help='do not scale histograms to unity')
    args = parser.parse_args()

    CombineCommonSets('QCD',doStudies=True)     # True by default, but just to show it here
    CombineCommonSets('ttbar',doStudies=True)
    MakeRun2('QCD',doStudies=True)
    MakeRun2('ttbar',doStudies=True)
    MakeRun2Signal()    # will only run once

    # if the keys of this dict already exist as histo names in the selected ROOT file, it'll use these names. 
    # else, it'll use the histo names
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
        # we want to ignore all histos with CR/SR in the name, since these will be handled by MXvsMY_plotter script
        if ('SR' in h) or ('CR' in h):
            continue
	print('Plotting {}'.format(h))
	if h in histNames.keys():
	    plot(h,histNames[h],args.scale)
	else:
	    plot(h,h,args.scale)

    # now that the kinematics, N-1 and N-2 are done, just run XHYbbWW_MXvsMY_plotter.py 
    ExecuteCmd('python XHYbbWW_MXvsMY_plotter.py')

