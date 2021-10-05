import ROOT
from TIMBER.Analyzer import CutGroup, analyzer
from TIMBER.Tools.Common import CompileCpp, OpenJSON

# Helper file for dealing with .txt files containing NanoAOD file locs
def SplitUp(filename,npieces,nFiles=False):
    '''Take in a txt file name where the contents are root
    file names separated by new lines. Split up the files
    into N lists where N is `npieces` in the case that `nFiles == False`.
    In the case that `nFiles == True`, `npieces` is treated as the
    number of files to have per list.
    '''
    files = open(filename,'r').readlines()
    nfiles = len(files)

    if npieces > nfiles:
        npieces = nfiles
    
    if not nFiles: files_per_piece = float(nfiles)/float(npieces)
    else: files_per_piece = npieces
    
    out = []
    iend = 0
    for ipiece in range(1,npieces+1):
        piece = []
        for ifile in range(iend,min(nfiles,int(ipiece*files_per_piece))):
            piece.append(files[ifile].strip())

        iend = int(ipiece*files_per_piece)
        out.append(piece)
    return out

class XHYbbWW:
    def __init__(self, inputfile, year, ijob, njobs):
        if inputfile.endswith('.txt'):
            infiles = SplitUp(inputfile, njobs)[ijob-1]
        else:
            infiles = inputfile

        #self.a = analyzer(infiles)

        if inputfile.endswith('.txt'):
	    # we're looking at signal
            if 'XYH_WWbb' in inputfile:
		# format is (raw_nano/XYH_WWbb_MX_<XMASS>_MY_<YMASS>_loc.txt
		prefix = inputfile.split('/')[-1].split('_')   # [XYH, WWbb, MX, <XMASS>, MY, <YMASS>, loc.txt]
		self.setname = (prefix[2] + '_' + prefix[3] + '_' + prefix[4] + '_' + prefix[5])  # MX_XMASS_MY_YMASS
	        # create an analyzer module with the proper multiSampleStr argument
		self.a = analyzer(infiles,multiSampleStr=prefix[5])
		# ensure we're working with the proper YMass
		self.a.Cut('CorrectMass', 'GenModel_YMass_{} == 1'.format(prefix[5]))
	    elif inputfile.startswith('trijet_nano'):    # this condition is met when we are running XHYbbWW_studies.py
		# format is "trijet_nano/setname_era_snapshot.txt"
		prefix = inputfile.split('/')[-1]   # everything after "trijet_nano"
		if 'MX' in prefix:    # signal setname is different from other setnames
		    s = prefix.split('_')
		    self.setname = ('{}_{}_{}_{}'.format(s[0],s[1],s[2],s[3]))    # MX_XMASS_MY_YMASS
		    self.a = analyzer(infiles,multiSampleStr=s[3])
		    #self.a.Cut('CorrectMass', 'GenModel_YMass_{} == 1'.format(s[3]))
		else:
		    self.setname = prefix.split('_')[0]
		    self.a = analyzer(infiles)
	    else:
		# format is (raw_nano/setname_era.txt)
		self.setname = inputfile.split('/')[-1].split('_')[0]
		self.a = analyzer(infiles)
        else:	# not likely to encounter this for this analysis
            self.setname = inputfile.split('/')[-1].split('_')[1]
	    self.a = analyzer(infiles)
        
        self.year = year
        self.ijob = ijob
        self.njobs = njobs
        
	# get config from JSON
	self.config = OpenJSON('XHYbbWWconfig.json')
	self.cuts = self.config['CUTS']

        # check if data or sim
        if 'Data' in inputfile:
            self.a.isData = True
        else:
            self.a.isData = False
            
    # for creating snapshots
    def kinematic_cuts(self):
        self.a.Cut('FatJet_cut', 'nFatJet > 2')     # we want at least 3 fatJets
        self.a.Cut('pt_cut', 'FatJet_pt[0] > 400 && FatJet_pt[1] > 200 && FatJet_pt[2] > 200')      # jets ordered by pt
        self.a.Cut('eta_cut', 'abs(FatJet_eta[0]) < 2.4 && abs(FatJet_eta[1]) < 2.4 && abs(FatJet_eta[2]) < 2.4')   # no super forward jets
        self.a.Cut('msoftdop_cut','FatJet_msoftdrop[0] > 50 && FatJet_msoftdrop[1] > 40 && FatJet_msoftdrop[2] > 40') # should always use softdrop mass
        self.a.Define('TrijetIdxs','ROOT::VecOps::RVec({0,1,2})')   # create a vector of the three jets - assume Higgs & Ws will be 3 leading jets
	# now we make a subcollection, which maps all branches with "FatJet" to a new subcollection named "Trijet", in this case
	# we specify that the Trijet indices are given by the TrijetIdxs vector above
	self.a.SubCollection('Trijet','FatJet','TrijetIdxs',useTake=True)
        return self.a.GetActiveNode()
        
    # for creating snapshots
    def Snapshot(self, node=None):
        startNode = self.a.GetActiveNode()
        if node == None:
            node = self.a.GetActiveNode()
        
        columns = [
        'Trijet_eta','Trijet_msoftdrop','Trijet_pt','Trijet_phi',
        'Trijet_deepTagMD_HbbvsQCD', 'Trijet_deepTagMD_ZHbbvsQCD',
        'Trijet_deepTagMD_WvsQCD', 'Trijet_deepTag_TvsQCD', 'Trijet_particleNet_HbbvsQCD',
        'Trijet_particleNet_TvsQCD', 'Trijet_particleNetMD.*', 'Trijet_rawFactor', 'Trijet_tau*',
        'Trijet_jetId', 'nTrijet', 'Trijet_JES_nom','Trijet_particleNetMD_Xqq',
        'Trijet_particleNet_WvsQCD','HLT_PFHT.*', 'HLT_PFJet.*', 'HLT_AK8.*', 'HLT_Mu50',
        'event', 'eventWeight', 'luminosityBlock', 'run']
        
        # append to columns list if not Data
        if not self.a.isData:
            columns.extend(['GenPart_.*', 'nGenPart','genWeight'])
            
        # get ready to send out snapshot
        self.a.Snapshot(columns, 'HWWsnapshot_{}_{}_{}of{}.root'.format(self.setname,self.year,self.ijob,self.njobs),'Events', openOption='RECREATE')
        self.a.SetActiveNode(startNode)
        
    # xsecs from JSON config file
    def GetXsecScale(self):	
	lumi = self.config['lumi{}'.format(self.year)]
	xsec = self.config['XSECS'][self.setname]
	if self.a.genEventSumw == 0:
	    raise ValueError('{} {}: genEventSumw is 0'.format(self.setname, self.year))
        return lumi*xsec/self.a.genEventSumw

    # N-1 group - this returns a dict of nodes, where each node is such that it has all but one of the cuts applied. 
    # used in order to see the effect of varying the tagger on selection
    def GetNminus1Group(self,tagger):
	cutgroup = CutGroup('taggingVars')
	# inside the studies code, we'll have made SubCollections called LeadHiggs, LeadW, SubleadW
	# first, cuts based on softdrop mass
	cutgroup.Add('mH_{}_cut'.format(tagger),'LeadHiggs_msoftdrop > {0} && LeadHiggs_msoftdrop < {1}'.format(*self.cuts['mh']))
	cutgroup.Add('mW1_{}_cut'.format(tagger),'LeadW_msoftdrop > {0} && LeadW_msoftdrop < {1}'.format(*self.cuts['mw']))
	cutgroup.Add('mW2_{}_cut'.format(tagger),'SubleadW_msoftdrop > {0} && SubleadW_msoftdrop < {1}'.format(*self.cuts['mw']))
	# now, cuts based on particleNet scores (for now, don't use mass-decorrelated)
	# taggers are: particleNet_HbbvsQCD, particleNet_WvsQCD
	cutgroup.Add('{}_H_cut'.format(tagger),'LeadHiggs_{0}_HbbvsQCD > {1}'.format(tagger, self.cuts[tagger+'_HbbvsQCD']))
	cutgroup.Add('{}_W1_cut'.format(tagger),'LeadW_{0}_WvsQCD > {1}'.format(tagger, self.cuts[tagger+'_WvsQCD']))
	cutgroup.Add('{}_W2_cut'.format(tagger),'SubleadW_{0}_WvsQCD > {1}'.format(tagger, self.cuts[tagger+'_WvsQCD']))
	return cutgroup

    # N-2 group - in this case we want to plot the Higgs tag cut after *all* cuts are made EXCEPT for the Higgs mass cut
    def GetNminus2Group(self,tagger):
	cutgroup = CutGroup('taggingVars')
	# we want to add every cut EXCEPT for higgs mass cut. Starting with mass cuts:
	cutgroup.Add('mW1_{}_cut'.format(tagger),'LeadW_msoftdrop > {0} && LeadW_msoftdrop < {1}'.format(*self.cuts['mw']))
        cutgroup.Add('mW2_{}_cut'.format(tagger),'SubleadW_msoftdrop > {0} && SubleadW_msoftdrop < {1}'.format(*self.cuts['mw']))
	# now we want to make cuts on particleNet scores (including Higgs tagger score)
	# after we call this function, we will grab the key that ends with 'H_cut'
        cutgroup.Add('{}_H_cut'.format(tagger),'LeadHiggs_{0}_HbbvsQCD > {1}'.format(tagger, self.cuts[tagger+'_HbbvsQCD']))
        cutgroup.Add('{}_W1_cut'.format(tagger),'LeadW_{0}_WvsQCD > {1}'.format(tagger, self.cuts[tagger+'_WvsQCD']))
        cutgroup.Add('{}_W2_cut'.format(tagger),'SubleadW_{0}_WvsQCD > {1}'.format(tagger, self.cuts[tagger+'_WvsQCD']))
	return cutgroup

    # for comparing mX vs mY
    def MXvsMY(self, tagger, Hbb=[0.8,0.98], W=[0.8]):
        '''
        We are plotting mX vs mY for QCD, ttbar, and signal (2000,800)
        Therefore we want to perform all kinematic cuts, all W&H mass cuts, and one of the scores constant while varying the other
	    ex: Keep WvsQCD constant at > 0.8, look in regions Hbb<0.8, 0.8<Hbb<0.98, Hbb>0.98
        We are looking at three regions, so let's return three cutgroups


	Let's also consider the second case where we're loosening our W cuts, say: 0.3 < W < 0.8
	We are keeping these cuts constant across all the varying H regions 
        '''
        # every cut, but 0 < Hbb < Hbb[0]
        region1 = CutGroup('region1')
	# mass cuts
        region1.Add('MXvsMY_mH_{}_cut'.format(tagger),'LeadHiggs_msoftdrop > {0} && LeadHiggs_msoftdrop < {1}'.format(*self.cuts['mh']))
        region1.Add('MXvsMY_mW1_{}_cut'.format(tagger),'LeadW_msoftdrop > {0} && LeadW_msoftdrop < {1}'.format(*self.cuts['mw']))
        region1.Add('MXvsMY_mW2_{}_cut'.format(tagger),'SubleadW_msoftdrop > {0} && SubleadW_msoftdrop < {1}'.format(*self.cuts['mw']))
	if (len(Hbb) > len(W)):    # we are using tight W cut 
            # W score cuts 
            region1.Add('MXvsMY_{}_W1_cut'.format(tagger),'LeadW_{0}_WvsQCD > {1}'.format(tagger, W[0])) 
            region1.Add('MXvsMY_{}_W2_cut'.format(tagger),'SubleadW_{0}_WvsQCD > {1}'.format(tagger, W[0]))
	    # H score in the specified region
	    region1.Add('MXvsMY_{}_H_cut'.format(tagger),'LeadHiggs_{0}_HbbvsQCD < {1}'.format(tagger, Hbb[0])) 
        else:		# we are using loose W cut, in a region W[0] < WvsQCD < W[1]
            region1.Add('MXvsMY_{}_W1_cut'.format(tagger),'LeadW_{0}_WvsQCD > {1} && LeadW_{0}_WvsQCD < {2}'.format(tagger, W[0], W[1]))
            region1.Add('MXvsMY_{}_W2_cut'.format(tagger),'SubleadW_{0}_WvsQCD > {1} && SubleadW_{0}_WvsQCD < {2}'.format(tagger, W[0], W[1]))
            region1.Add('MXvsMY_{}_H_cut'.format(tagger),'LeadHiggs_{0}_HbbvsQCD < {1}'.format(tagger, Hbb[0]))

	# every cut, but Hbb[0] < Hbb < Hbb[1]
	region2 = CutGroup('region2')
        region2.Add('MXvsMY_mH_{}_cut'.format(tagger),'LeadHiggs_msoftdrop > {0} && LeadHiggs_msoftdrop < {1}'.format(*self.cuts['mh']))
	region2.Add('MXvsMY_mW1_{}_cut'.format(tagger),'LeadW_msoftdrop > {0} && LeadW_msoftdrop < {1}'.format(*self.cuts['mw']))
	region2.Add('MXvsMY_mW2_{}_cut'.format(tagger),'SubleadW_msoftdrop > {0} && SubleadW_msoftdrop < {1}'.format(*self.cuts['mw']))
	if (len(Hbb) > len(W)):
            region2.Add('MXvsMY_{}_W1_cut'.format(tagger),'LeadW_{0}_WvsQCD > {1}'.format(tagger, W[0]))
            region2.Add('MXvsMY_{}_W2_cut'.format(tagger),'SubleadW_{0}_WvsQCD > {1}'.format(tagger, W[0]))
            region2.Add('MXvsMY_{}_H_cut'.format(tagger),'LeadHiggs_{0}_HbbvsQCD > {1} && LeadHiggs_{0}_HbbvsQCD < {2}'.format(tagger, Hbb[0], Hbb[1]))
	else:
            region2.Add('MXvsMY_{}_W1_cut'.format(tagger),'LeadW_{0}_WvsQCD > {1} && LeadW_{0}_WvsQCD < {2}'.format(tagger, W[0], W[1]))
            region2.Add('MXvsMY_{}_W2_cut'.format(tagger),'SubleadW_{0}_WvsQCD > {1} && SubleadW_{0}_WvsQCD < {2}'.format(tagger, W[0], W[1]))
            region2.Add('MXvsMY_{}_H_cut'.format(tagger),'LeadHiggs_{0}_HbbvsQCD > {1} && LeadHiggs_{0}_HbbvsQCD < {2}'.format(tagger, Hbb[0], Hbb[1]))

	# every cut but Hbb > Hbb[1]
	region3 = CutGroup('region3')
        region3.Add('MXvsMY_mH_{}_cut'.format(tagger),'LeadHiggs_msoftdrop > {0} && LeadHiggs_msoftdrop < {1}'.format(*self.cuts['mh']))
	region3.Add('MXvsMY_mW1_{}_cut'.format(tagger),'LeadW_msoftdrop > {0} && LeadW_msoftdrop < {1}'.format(*self.cuts['mw']))
	region3.Add('MXvsMY_mW2_{}_cut'.format(tagger),'SubleadW_msoftdrop > {0} && SubleadW_msoftdrop < {1}'.format(*self.cuts['mw']))
	if (len(Hbb) > len(W)):
	    region3.Add('MXvsMY_{}_W1_cut'.format(tagger),'LeadW_{0}_WvsQCD > {1}'.format(tagger, W[0]))
	    region3.Add('MXvsMY_{}_W2_cut'.format(tagger),'SubleadW_{0}_WvsQCD > {1}'.format(tagger, W[0]))
	    region3.Add('MXvsMY_{}_H_cut'.format(tagger),'LeadHiggs_{0}_HbbvsQCD > {1}'.format(tagger, Hbb[1]))
	else:
	    region3.Add('MXvsMY_{}_W1_cut'.format(tagger),'LeadW_{0}_WvsQCD > {1} && LeadW_{0}_WvsQCD < {2}'.format(tagger, W[0], W[1]))
	    region3.Add('MXvsMY_{}_W2_cut'.format(tagger),'SubleadW_{0}_WvsQCD > {1} && SubleadW_{0}_WvsQCD < {2}'.format(tagger, W[0], W[1]))
	    region3.Add('MXvsMY_{}_H_cut'.format(tagger),'LeadHiggs_{0}_HbbvsQCD > {1}'.format(tagger, Hbb[1]))
	
	# return list (fixed order) of the three cutgroups, for use in XHYbbWW_studies.py
	return [region1, region2, region3]
