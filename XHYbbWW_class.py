import ROOT
from TIMBER.Analyzer import Correction, CutGroup, ModuleWorker, analyzer
from TIMBER.Tools.Common import CompileCpp, OpenJSON
from TIMBER.Tools.AutoPU import ApplyPU
from JMEvalsOnly import JMEvalsOnly
import TIMBER.Tools.AutoJME as AutoJME

AutoJME.AK8collection = 'Trijet'

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

	# triggers for various years
        self.trigs = {
            16:['HLT_PFHT800','HLT_PFHT900'],
            17:['HLT_PFHT1050','HLT_AK8PFJet500'],
            18:['HLT_AK8PFJet400_TrimMass30','HLT_AK8PFHT850_TrimMass50','HLT_PFHT1050']
        }

        # check if data or sim
        if 'Data' in inputfile:
            self.a.isData = True
        else:
            self.a.isData = False
           
    def AddCutflowColumn(self, var, varName):
	'''
	for future reference:
	https://root-forum.cern.ch/t/rdataframe-define-column-of-same-constant-value/34851
	'''
	print('Adding cutflow information...\n\t{}\t{}'.format(varName, var))
	self.a.Define('{}'.format(varName), str(var))
 
    def getNweighted(self):
	if not self.a.isData:
	    return self.a.DataFrame.Sum("genWeight").GetValue()
	else:
	    return self.a.DataFrame.Count().GetValue()

    # for creating snapshots
    def kinematic_cuts(self):
	self.NPROC = self.getNweighted()
	self.AddCutflowColumn(self.NPROC, "NPROC")

        self.a.Cut('FatJet_cut', 'nFatJet > 2')     # we want at least 3 fatJets
	self.NJETS = self.getNweighted()
	self.AddCutflowColumn(self.NJETS, "NJETS")

        self.a.Cut('pt_cut', 'FatJet_pt[0] > 400 && FatJet_pt[1] > 200 && FatJet_pt[2] > 200')      # jets ordered by pt
	self.NPT = self.getNweighted()
	self.AddCutflowColumn(self.NPT, "NPT")

        self.a.Cut('eta_cut', 'abs(FatJet_eta[0]) < 2.4 && abs(FatJet_eta[1]) < 2.4 && abs(FatJet_eta[2]) < 2.4')   # no super forward jets
	self.NETA = self.getNweighted()
	self.AddCutflowColumn(self.NETA, "NETA")

        self.a.Cut('msoftdop_cut','FatJet_msoftdrop[0] > 50 && FatJet_msoftdrop[1] > 40 && FatJet_msoftdrop[2] > 40') # should always use softdrop mass
	self.NMSD = self.getNweighted()
	self.AddCutflowColumn(self.NMSD, "NMSD")

        self.a.Define('TrijetIdxs','ROOT::VecOps::RVec({0,1,2})')   # create a vector of the three jets - assume Higgs & Ws will be 3 leading jets
	# now we make a subcollection, which maps all branches with "FatJet" to a new subcollection named "Trijet", in this case
	# we specify that the Trijet indices are given by the TrijetIdxs vector above
	self.a.SubCollection('Trijet','FatJet','TrijetIdxs',useTake=True)
        return self.a.GetActiveNode()
       
    # corrections - used in both snapshots and selection
    def ApplyStandardCorrections(self, snapshot=False):
	# first apply corrections for snapshot phase
	if snapshot:
	    if self.a.isData:
		# instantiate ModuleWorker to handle the C++ code via clang
		lumiFilter = ModuleWorker('LumiFilter','TIMBER/Framework/include/LumiFilter.h',[int(self.year) if 'APV' not in self.year else 16])    # defaults to perform "eval" method 
		self.a.Cut('lumiFilter',lumiFilter.GetCall(evalArgs={"lumi":"luminosityBlock"}))	       # replace lumi with luminosityBlock
		if self.year == 18:
		    HEM_worker = ModuleWorker('HEM_drop','TIMBER/Framework/include/HEM_drop.h',[self.setname])
		    self.a.Cut('HEM','%s[0] > 0'%(HEM_worker.GetCall(evalArgs={"FatJet_eta":"Trijet_eta","FatJet_phi":"Trijet_phi"})))
	    else:
		# OLD - Pre-NanoAODv9 Rules
		# XHYbbWWpileup.root must be created before running snapshot - run XHYbbWWpileup.py
		#self.a = ApplyPU(self.a,'20{}UL'.format(self.year), 'XHYbbWWpileup.root', '{}_{}'.format(self.setname,self.year))
	
		# updated to latest version of TIMBER
		# ApplyPU(a, filename, year, ULflag=True, histname='autoPU')    -  filename: name of pileup file created from XHYbbWWpileup.py
		self.a = ApplyPU(self.a, 'XHYbbWWpileup.root', self.year, ULflag=True, histname='{}_{}'.format(self.setname,self.year))

		#self.a.AddCorrection(Correction('HEM_drop','TIMBER/Framework/include/HEM_drop.h',[self.setname],corrtype='corr'))
		if self.year == 16 or self.year == 17:
		    self.a.AddCorrection(Correction("Prefire","TIMBER/Framework/include/Prefire_weight.h",[self.year],corrtype='weight'))
		elif self.year == 18:
		    self.a.AddCorrection(Correction('HEM_drop','TIMBER/Framework/include/HEM_drop.h',[self.setname],corrtype='corr'))
	    #JMEvalsOnly(self.a, 'Trijet', str(2000+self.year), self.setname)
	    self.a = AutoJME.AutoJME(self.a, 'Trijet', self.year, self.setname)
	    self.a.MakeWeightCols(extraNominal='genWeight' if not self.a.isData else '')

	# now for selection
	else:
	    if not self.a.isData:
		self.a.AddCorrection(Correction('Pileup',corrtype='weight'))
		self.a.AddCorrection(Correction('Pdfweight',corrtype='uncert'))
                if self.year == 16 or self.year == 17:
                    self.a.AddCorrection(Correction('Prefire',corrtype='weight'))
                elif self.year == 18:
                    self.a.AddCorrection(Correction('HEM_drop',corrtype='corr'))
                #if 'ttbar' in self.setname:
                    #self.a.AddCorrection(Correction('TptReweight',corrtype='weight'))
	return self.a.GetActiveNode()

    # for selection purposes - used for making templates for 2DAlphabet
    def OpenForSelection(self, variation):
	self.ApplyStandardCorrections(snapshot=False)
	# for trigger effs
	self.a.Define('Trijet_vect_trig','hardware::TLvector(Trijet_pt, Trijet_eta, Trijet_phi, Trijet_msoftdrop)')
	self.a.Define('mhww_trig','hardware::InvariantMass(Trijet_vect_trig)')
	self.a.Define('m_javg','(Trijet_msoftdrop[0]+Trijet_msoftdrop[1]+Trijet_msoftdrop[2])/3')
	# JME variations - we only do this for signal (think about how)
	if not self.a.isData:
	    # since H, W close enough in mass, we can treat them the same. 
	    # Higgs, W will have same pt and mass calibrations
	    pt_calibs, mass_calibs = JMEvariationStr('Higgs',variation)
	    self.a.Define('Trijet_pt_corr','hardware::MultiHadamardProduct(Trijet_pt,{})'.format(pt_calibs))
	    self.a.Define('Trijet_msoftdrop_corr','hardware::MultiHadamardProduct(Trijet_msoftdrop,{})'.format(mass_calibs))
	else:
	    self.a.Define('Trijet_pt_corr','hardware::MultiHadamardProduct(Trijet_pt,{Trijet_JES_nom})')
	    self.a.Define('Trijet_msoftdrop_corr','hardware::MultiHadamardProduct(Trijet_msoftdrop,{Trijet_JES_nom})')
	return self.a.GetActiveNode()

    # for trigger effs
    def ApplyTrigs(self, corr=None):
	if self.a.isData:
	    self.a.Cut('trigger',self.a.GetTriggerString(self.trigs[int(self.year) if 'APV' not in self.year else 16]))
	else:
	    self.a.AddCorrection(corr, evalArgs={"xval":"m_javg","yval":"mhww_trig"})
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
        'event', 'eventWeight', 'luminosityBlock', 'run',
	'NPROC', 'NJETS', 'NPT', 'NETA', 'NMSD']
        
        # append to columns list if not Data
        if not self.a.isData:
            columns.extend(['GenPart_.*', 'nGenPart','genWeight'])
	    columns.extend(['Trijet_JES_up','Trijet_JES_down',
			    'Trijet_JER_nom','Trijet_JER_up','Trijet_JER_down',
			    'Trijet_JMS_nom','Trijet_JMS_up','Trijet_JMS_down',
			    'Trijet_JMR_nom','Trijet_JMR_up','Trijet_JMR_down'])
	    columns.extend(['Pileup__nom','Pileup__up','Pileup__down','Pdfweight__nom','Pdfweight__up','Pdfweight__down'])
	    if self.year == 16 or self.year == 16:
		columns.extend(['Prefire__nom','Prefire__up','Prefire__down'])
	    elif self.year == 18:
		columns.append('HEM_drop__nom')
            
        # get ready to send out snapshot
        #self.a.SetActiveNode(node)
        self.a.Snapshot(columns, 'HWWsnapshot_{}_{}_{}of{}.root'.format(self.setname,self.year,self.ijob,self.njobs),'Events', openOption='RECREATE',saveRunChain=True)
        self.a.SetActiveNode(startNode)
        
    # xsecs from JSON config file
    def GetXsecScale(self):	
	lumi = self.config['lumi{}'.format(self.year if 'APV' not in self.year else 16)]
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
		- fail:		Hbb < 0.8
		- loose: 	0.8 < Hbb < 0.98
		- tight: 	Hbb > 0.98
	Let's also consider the second case where we're loosening our W cuts, say: 0.3 < W < 0.8
	We are keeping these cuts constant across all the varying H regions 
        '''
        # every cut, but 0 < Hbb < Hbb[0]
	# --------------------------------------
	# 		Higgs Fail
	# --------------------------------------
        region1 = CutGroup('region1')
	# mass cuts
        region1.Add('MXvsMY_mH_{}_cut'.format(tagger),'LeadHiggs_msoftdrop > {0} && LeadHiggs_msoftdrop < {1}'.format(*self.cuts['mh']))
        region1.Add('MXvsMY_mW1_{}_cut'.format(tagger),'LeadW_msoftdrop > {0} && LeadW_msoftdrop < {1}'.format(*self.cuts['mw']))
        region1.Add('MXvsMY_mW2_{}_cut'.format(tagger),'SubleadW_msoftdrop > {0} && SubleadW_msoftdrop < {1}'.format(*self.cuts['mw']))
	if (len(Hbb) > len(W)):    # we are using tight W cut 	- AKA SIGNAL REGION
            # W score cuts 
            region1.Add('MXvsMY_{}_W1_cut'.format(tagger),'LeadW_{0}_WvsQCD > {1}'.format(tagger, W[0])) 
            region1.Add('MXvsMY_{}_W2_cut'.format(tagger),'SubleadW_{0}_WvsQCD > {1}'.format(tagger, W[0]))
	    # H score in the specified region
	    region1.Add('MXvsMY_{}_H_cut'.format(tagger),'LeadHiggs_{0}_HbbvsQCD < {1}'.format(tagger, Hbb[0])) 
        else:		# we are using loose W cut, in a region W[0] < WvsQCD < W[1]	- AKA CONTROL REGION
            region1.Add('MXvsMY_{}_W1_cut'.format(tagger),'LeadW_{0}_WvsQCD > {1} && LeadW_{0}_WvsQCD < {2}'.format(tagger, W[0], W[1]))
            region1.Add('MXvsMY_{}_W2_cut'.format(tagger),'SubleadW_{0}_WvsQCD > {1} && SubleadW_{0}_WvsQCD < {2}'.format(tagger, W[0], W[1]))
            region1.Add('MXvsMY_{}_H_cut'.format(tagger),'LeadHiggs_{0}_HbbvsQCD < {1}'.format(tagger, Hbb[0]))

	# every cut, but Hbb[0] < Hbb < Hbb[1]
	# --------------------------------------------
	# 		Higgs Loose
	# --------------------------------------------
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
	# -----------------------------------------------
	# 		Higgs Pass
	# -----------------------------------------------
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


    # new functions to be used in selection 
    def ApplyMassCuts(self):
	# perform Higgs mass window cut, save cutflow info
	self.a.Cut('mH_{}_cut'.format('window'),'LeadHiggs_msoftdrop > {0} && LeadHiggs_msoftdrop < {1}'.format(*self.cuts['mh']))
	self.nHiggs = self.getNweighted()
	self.AddCutflowColumn(self.nHiggs, 'nHiggsMassCut')
	# Lead W mass window cut, cutflow
	self.a.Cut('mW1_{}_cut'.format('window'),'LeadW_msoftdrop > {0} && LeadW_msoftdrop < {1}'.format(*self.cuts['mw']))
	self.nW1 = self.getNweighted()
	self.AddCutflowColumn(self.nW1, 'nW1MassCut')
	# sublead W
	self.a.Cut('mW2_{}_cut'.format('window'),'SubleadW_msoftdrop > {0} && SubleadW_msoftdrop > {1}'.format(*self.cuts['mw']))
	self.nW2 = self.getNweighted()
	self.AddCutflowColumn(self.nW2, 'nW2MassCut')
	return self.a.GetActiveNode()

    def ApplyWTag(self, SRorCR, tagger):
	'''
	SRorCR [str] = 'SR' or 'CR', used to generate cutflow information
	tagger [str] = name of tagger to be used 

	W tagging criteria:
		SR: W > 0.8
		CR: 0.05 < W < 0.8
	'''
	assert(SRorCR=='SR' or SRorCR=='CR')
	# tagger values for each 
	W_CR = [0.05, 0.8]
        W_SR = 0.8
	if SRorCR == 'SR':
	    self.a.Cut('W1_{}_cut_{}'.format(tagger,SRorCR), 'LeadW_{0} > {1}'.format(tagger,W_SR))
	    self.a.Cut('W2_{}_cut_{}'.format(tagger,SRorCR), 'SubleadW_{0} > {1}'.format(tagger,W_SR))
	else:
	    self.a.Cut('W1_{}_cut_{}'.format(tagger,SRorCR), 'LeadW_{0} > {1} && LeadW_{0} < {2}'.format(tagger,*W_CR))
	    self.a.Cut('W2_{}_cut_{}'.format(tagger,SRorCR), 'SubleadW_{0} > {1} && SubleadW_{0} < {2}'.format(tagger,*W_CR))
	# save cutflow info
	self.nWTag = self.getNweighted()
	self.AddCutflowColumn(self.nWTag, 'nWTag_{}'.format(SRorCR))
	return self.GetActiveNode()

    def ApplyHiggsTag(self, SRorCR, tagger):
	'''
	Fail:	H < 0.8
	Loose:	0.8 < H < 0.98
	Pass: 	H > 0.98
	'''
	assert(SRorCR=='SR' or SRorCR=='CR')
	checkpoint = self.a.GetActiveNode()
	cuts = [0.8, 0.98]
	FLP = {}
	# Higgs fail + cutflow info
	FLP['fail'] = self.a.Cut('HbbTag_fail','Higgs_{0} < {1}'.format(tagger, cuts[0]))
	self.nHF = self.getNweighted()
	self.AddCutflowColumn(self.nHF, 'higgsF_{}'.format(SRorCR))
	# Higgs Loose + cutflow
	self.a.SetActiveNode(checkpoint)
	FLP['loose'] = self.a.Cut('HbbTag_loose','Higgs_{0} > {1} && Higgs{0} < {2}'.format(tagger, *cuts))
	self.nHL = self.getNweighted()
	self.AddCutflowColumn(self.nHL, 'higgsL_{}'.format(SRorCR))
	# Higgs Pass + cutflow
	self.a.SetActiveNode(checkpoint)
	FLP['pass'] = self.a.Cut('HbbTag_pass','Higgs_{0} > {1}'.format(tagger, cuts[1]))
	self.nHP = self.getNweighted()
	self.AddCutflowColumn(self.nHP, 'higgsP_{}'.format(SRorCR))
	# reset state, return dict
	self.a.SetActiveNode(checkpoint)
	return FLP
	

# for use in selection - essentially just creates combinations of all the JME variations
def JMEvariationStr(p, variation):
    base_calibs = ['Trijet_JES_nom','Trijet_JER_nom','Trijet_JMS_nom','Trijet_JMR_nom']
    variationType = variation.split('_')[0]
    pt_calib_vect = '{'
    mass_calib_vect = '{'
    for c in base_calibs:
	if 'JM' in c and p != 'Top':	# 'Top' will never be in p, but just leave this
	    mass_calib_vect += '%s,'%('Trijet_'+variation if variationType in c else c)
	elif 'JE' in c:
	    pt_calib_vect += '%s,'%('Trijet_'+variation if variationType in c else c)
	    mass_calib_vect += '%s,'%('Trijet_'+variation if variationType in c else c)
    pt_calib_vect = pt_calib_vect[:-1]+'}'
    mass_calib_vect = mass_calib_vect[:-1]+'}'
    return pt_calib_vect, mass_calib_vect



