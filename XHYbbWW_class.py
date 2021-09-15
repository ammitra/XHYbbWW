import ROOT
from TIMBER.Analyzer import CutGroup, analyzer
from TIMBER.Tools.Common import CompileCpp

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
	self.a.SubCollection('Trijet','FatJet','TrijetIdxs',useTake=True) # takes every attribute of FatJet and replace with "Trijet" -> then this is used in columns for Snapshot()
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
        

