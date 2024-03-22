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

	self.setname = inputfile.split('/')[-1].split('_')[0]
        self.a = analyzer(infiles)
        
        self.year = str(year)
        self.ijob = ijob
        self.njobs = njobs
        
	# get config from JSON
	self.config = OpenJSON('XHYbbWWconfig.json')
	self.cuts = self.config['CUTS']

	# triggers for various years
        self.trigs = {
            #'16':['HLT_PFHT800','HLT_PFHT900'],
            #'17':['HLT_PFHT1050','HLT_AK8PFJet500'],
            #'18':['HLT_AK8PFJet400_TrimMass30','HLT_AK8PFHT850_TrimMass50','HLT_PFHT1050']
	    16:['HLT_PFHT800','HLT_PFHT900'],
	    17:["HLT_PFHT1050","HLT_AK8PFJet500","HLT_AK8PFHT750_TrimMass50","HLT_AK8PFHT800_TrimMass50","HLT_AK8PFJet400_TrimMass30"],
	    18:['HLT_AK8PFJet400_TrimMass30','HLT_AK8PFHT850_TrimMass50','HLT_PFHT1050']
	    #16:['HLT_AK8PFJet360_TrimMass30','HLT_AK8PFJet450','HLT_PFHT800','HLT_PFHT900','HLT_PFJet450','HLT_AK8PFHT700_TrimR0p1PT0p03Mass50'],
	    #17:["HLT_PFHT1050","HLT_AK8PFJet500","HLT_AK8PFHT750_TrimMass50","HLT_AK8PFHT800_TrimMass50","HLT_AK8PFJet400_TrimMass30","HLT_PFJet500","HLT_AK8PFJet380_TrimMass30","HLT_AK8PFJet400_TrimMass30"],
	    #18:['HLT_AK8PFJet400_TrimMass30','HLT_AK8PFHT850_TrimMass50','HLT_PFHT1050','HLT_PFJet500','HLT_AK8PFJet330_TrimMass30_PFAK8BoostedDoubleB_np2','HLT_AK8PFJet400_TrimMass30']
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
    def ApplyKinematicsSnap(self):
	self.NPROC = self.getNweighted()
	self.AddCutflowColumn(self.NPROC, "NPROC")

	flags = [
	    'Flag_goodVertices',
	    'Flag_globalSuperTightHalo2016Filter',
	    'Flag_HBHENoiseFilter',
	    'Flag_HBHENoiseIsoFilter',
	    'Flag_EcalDeadCellTriggerPrimitiveFilter',
	    'Flag_BadPFMuonFilter',
	    'Flag_BadPFMuonDzFilter',
	    'Flag_eeBadScFilter'
	]
	if self.year == '17' or self.year == '18':
	    flags.append('Flag_ecalBadCalibFilter')
	MET_filters = self.a.GetFlagString(flags)	# string valid (existing in RDataFrame node) flags together w logical and
	self.a.Cut('flags', MET_filters)
	self.NFLAGS = self.getNweighted()
	self.AddCutflowColumn(self.NFLAGS, "NFLAGS")

        self.a.Cut('FatJet_cut', 'nFatJet > 2')     # we want at least 3 fatJets
	self.NJETS = self.getNweighted()
	self.AddCutflowColumn(self.NJETS, "NJETS")

        self.a.Cut('pt_cut', 'FatJet_pt[0] > 400 && FatJet_pt[1] > 200 && FatJet_pt[2] > 200')      # jets ordered by pt
	self.NPT = self.getNweighted()
	self.AddCutflowColumn(self.NPT, "NPT")

        self.a.Cut('eta_cut', 'abs(FatJet_eta[0]) < 2.4 && abs(FatJet_eta[1]) < 2.4 && abs(FatJet_eta[2]) < 2.4')   # no super forward jets
	self.NETA = self.getNweighted()
	self.AddCutflowColumn(self.NETA, "NETA")

        self.a.Cut('msoftdrop_cut','FatJet_msoftdrop[0] > 50 && FatJet_msoftdrop[1] > 40 && FatJet_msoftdrop[2] > 40') # should always use softdrop mass
	self.NMSD = self.getNweighted()
	self.AddCutflowColumn(self.NMSD, "NMSD")

        self.a.Define('TrijetIdxs','ROOT::VecOps::RVec({0,1,2})')   # create a vector of the three jets - assume Higgs & Ws will be 3 leading jets
	# now we make a subcollection, which maps all branches with "FatJet" to a new subcollection named "Trijet", in this case
	# we specify that the Trijet indices are given by the TrijetIdxs vector above
	self.a.SubCollection('Trijet','FatJet','TrijetIdxs',useTake=True)

	# now just look at the three jets selected and look at deltaR (angular difference) between each
	self.a.Define('jet0','ROOT::Math::PtEtaPhiMVector(Trijet_pt[0],Trijet_eta[0],Trijet_phi[0],Trijet_msoftdrop[0])')
        self.a.Define('jet1','ROOT::Math::PtEtaPhiMVector(Trijet_pt[1],Trijet_eta[1],Trijet_phi[1],Trijet_msoftdrop[1])')
        self.a.Define('jet2','ROOT::Math::PtEtaPhiMVector(Trijet_pt[2],Trijet_eta[2],Trijet_phi[2],Trijet_msoftdrop[2])')
        self.a.Define('jet0_mreg','ROOT::Math::PtEtaPhiMVector(Trijet_pt[0],Trijet_eta[0],Trijet_phi[0],Trijet_particleNet_mass[0])')
        self.a.Define('jet1_mreg','ROOT::Math::PtEtaPhiMVector(Trijet_pt[1],Trijet_eta[1],Trijet_phi[1],Trijet_particleNet_mass[1])')
        self.a.Define('jet2_mreg','ROOT::Math::PtEtaPhiMVector(Trijet_pt[2],Trijet_eta[2],Trijet_phi[2],Trijet_particleNet_mass[2])')
	self.a.Define('dR01','hardware::DeltaR(jet0,jet1)')
	self.a.Define('dR02','hardware::DeltaR(jet0,jet2)')
	self.a.Define('dR12','hardware::DeltaR(jet1,jet2)')
        self.a.Define('dR01_mreg','hardware::DeltaR(jet0_mreg,jet1_mreg)')
        self.a.Define('dR02_mreg','hardware::DeltaR(jet0_mreg,jet2_mreg)')
        self.a.Define('dR12_mreg','hardware::DeltaR(jet1_mreg,jet2_mreg)')
	return self.a.GetActiveNode()

    # corrections - used in both snapshots and selection
    def ApplyStandardCorrections(self, snapshot=False):
	# first apply corrections for snapshot phase	
	if snapshot:
	    # DATA - only filter valid lumi blocks and drop HEM-affected events
	    if self.a.isData:
		# NOTE: LumiFilter requires the year as an integer 
		lumiFilter = ModuleWorker('LumiFilter','TIMBER/Framework/include/LumiFilter.h',[int(self.year) if 'APV' not in self.year else 16])    # defaults to perform "eval" method 
		self.a.Cut('lumiFilter',lumiFilter.GetCall(evalArgs={"lumi":"luminosityBlock"}))	       # replace lumi with luminosityBlock
		if self.year == '18':
		    HEM_worker = ModuleWorker('HEM_drop','TIMBER/Framework/include/HEM_drop.h',[self.setname if 'Muon' not in self.setname else self.setname[10:]])
		    self.a.Cut('HEM','%s[0] > 0'%(HEM_worker.GetCall(evalArgs={"FatJet_eta":"Trijet_eta","FatJet_phi":"Trijet_phi"})))
	    # MC - apply corrections
	    else:
		# Parton shower weights 
		#	- https://twiki.cern.ch/twiki/bin/viewauth/CMS/TopSystematics#Parton_shower_uncertainties
		#	- "Default" variation: https://twiki.cern.ch/twiki/bin/view/CMS/HowToPDF#Which_set_of_weights_to_use
		#	- https://github.com/mroguljic/Hgamma/blob/409622121e8ab28bc1072c6d8981162baf46aebc/templateMaker.py#L210
		self.a.Define("ISR__up","PSWeight[2]")
		self.a.Define("ISR__down","PSWeight[0]")
		self.a.Define("FSR__up","PSWeight[3]")
		self.a.Define("FSR__down","PSWeight[1]")
		genWCorr    = Correction('genW','TIMBER/Framework/TopPhi_modules/BranchCorrection.cc',corrtype='corr',mainFunc='evalCorrection') # workaround so we can have multiple BCs
		self.a.AddCorrection(genWCorr, evalArgs={'val':'genWeight'})
		#ISRcorr = Correction('ISRunc', 'TIMBER/Framework/TopPhi_modules/BranchCorrection.cc', mainFunc='evalUncert', corrtype='uncert')
		#FSRcorr = Correction('FSRunc', 'TIMBER/Framework/TopPhi_modules/BranchCorrection.cc', mainFunc='evalUncert', corrtype='uncert')
		ISRcorr = genWCorr.Clone("ISRunc",newMainFunc="evalUncert",newType="uncert")
		FSRcorr = genWCorr.Clone("FSRunc",newMainFunc="evalUncert",newType="uncert")
		self.a.AddCorrection(ISRcorr, evalArgs={'valUp':'ISR__up','valDown':'ISR__down'})
		self.a.AddCorrection(FSRcorr, evalArgs={'valUp':'FSR__up','valDown':'FSR__down'})
		# Pileup reweighting
		self.a = ApplyPU(self.a, 'XHYbbWWpileup.root', '20{}'.format(self.year), ULflag=True, histname='{}_{}'.format(self.setname,self.year))
		# QCD factorization and renormalization corrections (only to non-signal MC)
		if 'NMSSM' not in self.setname:
		    # First instatiate a correction module for the factorization correction
		    facCorr = Correction('QCDscale_factorization','LHEScaleWeights.cc',corrtype='weight',mainFunc='evalFactorization')
		    self.a.AddCorrection(facCorr, evalArgs={'LHEScaleWeights':'LHEScaleWeight'})
		    # Now clone it and call evalRenormalization for the renormalization correction
		    renormCorr = facCorr.Clone('QCDscale_renormalization',newMainFunc='evalRenormalization',newType='weight')
		    self.a.AddCorrection(renormCorr, evalArgs={'LHEScaleWeights':'LHEScaleWeight'})
		    # Now do one for the combined correction
		    combCorr = facCorr.Clone('QCDscale_combined',newMainFunc='evalCombined',newType='weight')
		    self.a.AddCorrection(combCorr, evalArgs={'LHEScaleWeights':'LHEScaleWeight'})
		# PDF weight correction - https://twiki.cern.ch/twiki/bin/viewauth/CMS/TopSystematics#PDF
		if self.a.lhaid != -1:
		    print('PDFweight correction: LHAid = {}'.format(self.a.lhaid))
		    self.a.AddCorrection(
		    	Correction('Pdfweight','TIMBER/Framework/include/PDFweight_uncert.h',[self.a.lhaid],corrtype='uncert')
		    )
		# Level-1 prefire corrections
		if self.year == '16' or self.year == '17' or 'APV' in self.year:
		    #self.a.AddCorrection(Correction("Prefire","TIMBER/Framework/include/Prefire_weight.h",[self.year],corrtype='weight'))
		    #L1PreFiringWeight = Correction("L1PreFiringWeight","TIMBER/Framework/TopPhi_modules/BranchCorrection.cc",constructor=[],mainFunc='evalWeight',corrtype='weight',columnList=['L1PreFiringWeight_Nom','L1PreFiringWeight_Up','L1PreFiringWeight_Dn'])
		    L1PreFiringWeight = genWCorr.Clone('L1PreFireCorr',newMainFunc='evalWeight',newType='weight')
		    self.a.AddCorrection(L1PreFiringWeight, evalArgs={'val':'L1PreFiringWeight_Nom','valUp':'L1PreFiringWeight_Up','valDown':'L1PreFiringWeight_Dn'})
		# HEM drop to 2018 MC
		elif self.year == '18':
		    self.a.AddCorrection(Correction('HEM_drop','TIMBER/Framework/include/HEM_drop.h',[self.setname],corrtype='corr'))

	    # AutoJME rewritten to automatically do softdrop and regressed mass
	    self.a = AutoJME.AutoJME(self.a, 'Trijet', '20{}'.format(self.year), self.setname if 'Muon' not in self.setname else self.setname[10:])

	    #self.a.MakeWeightCols(extraNominal='genWeight' if not self.a.isData else '')
	    self.a.MakeWeightCols() # since we added genWcorr we do not have to do anything else with extraNominal genWeight correction

	# now for selection
	else:
	    if not self.a.isData:
		self.a.AddCorrection(Correction('Pileup',corrtype='weight'))
		self.a.AddCorrection(Correction('ISRunc',corrtype='uncert'))
		self.a.AddCorrection(Correction('FSRunc',corrtype='uncert'))
		if self.a.lhaid != -1: self.a.AddCorrection(Correction('Pdfweight',corrtype='uncert'))
		if 'NMSSM' not in self.setname:
		    self.a.AddCorrection(Correction('QCDscale_factorization',corrtype='weight'))
		    self.a.AddCorrection(Correction('QCDscale_renormalization',corrtype='weight'))
		    self.a.AddCorrection(Correction('QCDscale_combined',corrtype='weight'))
                if self.year == '16' or self.year == '17' or 'APV' in self.year:
		    # Instead, instantiate ModuleWorker to handle the C++ code via clang. This uses the branches already existing in NanoAODv9
		    self.a.AddCorrection(Correction('L1PreFiringWeight',corrtype='weight'))
                elif self.year == '18':
                    self.a.AddCorrection(Correction('HEM_drop',corrtype='corr'))

	return self.a.GetActiveNode()

    # for selection purposes - used for making templates for 2DAlphabet
    def OpenForSelection(self, variation):
	# Mass-decorrelated W tagger discriminant is defined by inclusion of X->cc 
	# See slide 16: https://indico.cern.ch/event/809820/contributions/3632617/attachments/1970786/3278138/MassDecorrelation_ML4Jets_H_Qu.pdf
	#self.a.Define('Trijet_particleNetMD_WvsQCD','Trijet_particleNetMD_Xqq/(Trijet_particleNetMD_Xqq+Trijet_particleNetMD_QCD)')
	self.a.Define('Trijet_particleNetMD_WvsQCD','(Trijet_particleNetMD_Xqq+Trijet_particleNetMD_Xcc)/(Trijet_particleNetMD_Xqq+Trijet_particleNetMD_Xcc+Trijet_particleNetMD_QCD)')
	self.a.Define('Trijet_particleNetMD_HbbvsQCD','Trijet_particleNetMD_Xbb/(Trijet_particleNetMD_Xbb+Trijet_particleNetMD_QCD)')
	self.ApplyStandardCorrections(snapshot=False)
	# for trigger effs
	self.a.Define('Trijet_vect_msoftdrop','hardware::TLvector(Trijet_pt, Trijet_eta, Trijet_phi, Trijet_msoftdrop)')
	self.a.Define('Trijet_vect_mregressed','hardware::TLvector(Trijet_pt, Trijet_eta, Trijet_phi, Trijet_particleNet_mass)')
	self.a.Define('mhww_msoftdrop_trig_precorr','hardware::InvariantMass(Trijet_vect_msoftdrop)')
	self.a.Define('mhww_mregressed_trig_precorr','hardware::InvariantMass(Trijet_vect_mregressed)')
	# naively consider the lead + sublead as the two Ws (higher pT), this will form our m_javg for trigger
	# we want trigger efficiency binned in ~mX vs ~mY -> mhww vs m_javg
	self.a.Define('m_javg_softdrop_precorr','(Trijet_msoftdrop[0]+Trijet_msoftdrop[1])/2')
	self.a.Define('m_javg_regressed_precorr','(Trijet_particleNet_mass[0]+Trijet_particleNet_mass[1])/2')
	# JME variations - we only do this for MC
	if not self.a.isData:
	    # since H, W close enough in mass, we can treat them the same. 
	    # Higgs, W will have same pt and mass calibrations
	    pt_calibs, softdrop_mass_calibs, regressed_mass_calibs = JMEvariationStr('Higgs',variation)
	    self.a.Define('Trijet_pt_corr','hardware::MultiHadamardProduct(Trijet_pt,{})'.format(pt_calibs))
	    self.a.Define('Trijet_msoftdrop_corr','hardware::MultiHadamardProduct(Trijet_msoftdrop,{})'.format(softdrop_mass_calibs))
	    self.a.Define('Trijet_mregressed_corr','hardware::MultiHadamardProduct(Trijet_particleNet_mass,{})'.format(regressed_mass_calibs))
	else:
	    self.a.Define('Trijet_pt_corr','hardware::MultiHadamardProduct(Trijet_pt,{Trijet_JES_nom})')
	    self.a.Define('Trijet_msoftdrop_corr','hardware::MultiHadamardProduct(Trijet_msoftdrop,{Trijet_JES_nom})')
	    self.a.Define('Trijet_mregressed_corr','hardware::MultiHadamardProduct(Trijet_particleNet_mass,{Trijet_JES_nom})')
	# make columns for the corrected masses
	self.a.Define('Trijet_vect_msoftdrop_corr','hardware::TLvector(Trijet_pt, Trijet_eta, Trijet_phi, Trijet_msoftdrop_corr)')
	self.a.Define('Trijet_vect_mregressed_corr','hardware::TLvector(Trijet_pt, Trijet_eta, Trijet_phi, Trijet_mregressed_corr)')
	self.a.Define('mhww_msoftdrop_trig_corr','hardware::InvariantMass(Trijet_vect_msoftdrop_corr)')
	self.a.Define('hhww_regressed_trig_corr','hardware::InvariantMass(Trijet_vect_mregressed_corr)')
        self.a.Define('m_javg_softdrop_corr','(Trijet_msoftdrop_corr[0]+Trijet_msoftdrop_corr[1])/2')
        self.a.Define('m_javg_regressed_corr','(Trijet_mregressed_corr[0]+Trijet_mregressed_corr[1])/2')
	# for trigger studies
	self.a.Define('pt0','Trijet_pt_corr[0]')
        self.a.Define('pt1','Trijet_pt_corr[1]')
        self.a.Define('pt2','Trijet_pt_corr[2]')
	self.a.Define('HT','pt0+pt1+pt2')
	return self.a.GetActiveNode()

    # for trigger effs
    def ApplyTrigs(self, corr=None, applyToMC=False):
	if (self.a.isData) or (applyToMC):
	    self.a.Cut('trigger',self.a.GetTriggerString(self.trigs[int(self.year) if 'APV' not in self.year else 16]))
	else:
	    # use the values before H/WW identification (aka the 'trig' values)
	    self.a.AddCorrection(corr, evalArgs={"xval":"mhww_msoftdrop_trig_precorr","yval":"m_javg_softdrop_precorr"})
	return self.a.GetActiveNode()

    # for creating snapshots
    def Snapshot(self, node=None):
        startNode = self.a.GetActiveNode()
        if node == None:
            node = self.a.GetActiveNode()
        
        columns = [
	#'FatJet_J*',	# this will collect all the JME variations created during snapshotting and used in selection 
        'Trijet_eta','Trijet_msoftdrop','Trijet_pt','Trijet_phi','Trijet_particleNet_mass',
        'Trijet_deepTagMD_HbbvsQCD', 'Trijet_deepTagMD_ZHbbvsQCD',
        'Trijet_deepTagMD_WvsQCD', 'Trijet_deepTag_TvsQCD', 'Trijet_particleNet_HbbvsQCD',
        'Trijet_particleNet_TvsQCD', 'Trijet_particleNetMD.*', 'Trijet_rawFactor', 'Trijet_tau*',
        'Trijet_jetId', 'nTrijet', 'Trijet_JES_nom','Trijet_particleNetMD_Xqq',
	'Trijet_particleNetMD_Xcc', 'Trijet_particleNet_QCD',
        'Trijet_particleNet_WvsQCD','HLT_PFHT.*', 'HLT_PFJet.*', 'HLT_AK8.*', 'HLT_Mu50',
        'event', 'eventWeight', 'luminosityBlock', 'run',
	'jet0','jet1','jet2','dR01','dR02','dR12',
	'NPROC', 'NJETS', 'NPT', 'NETA', 'NMSD'] # cutflow information
        
        # append to columns list if not Data
        if not self.a.isData:
            columns.extend(['GenPart_.*', 'nGenPart', 'genWeight', 'GenModel*'])
	    columns.extend(['PSWeight', 'LHEScaleWeight']) # for parton shower (ISR+FSR) and QCD renormalization and factorization scale uncertainties
	    columns.extend(['Trijet_JES_up','Trijet_JES_down',
			    'Trijet_JER_nom','Trijet_JER_up','Trijet_JER_down',
			    'Trijet_JMS_nom','Trijet_JMS_up','Trijet_JMS_down', # no longer exists
			    'Trijet_JMR_nom','Trijet_JMR_up','Trijet_JMR_down', # no longer exists
			    'Trijet_JMS_regressed_nom','Trijet_JMS_regressed_up','Trijet_JMS_regressed_down',
			    'Trijet_JMR_regressed_nom','Trijet_JMR_regressed_up','Trijet_JMR_regressed_down',
			    'Trijet_JMS_softdrop_nom','Trijet_JMS_softdrop_up','Trijet_JMS_softdrop_down',
			    'Trijet_JMR_softdrop_nom','Trijet_JMR_softdrop_up','Trijet_JMR_softdrop_down'])
	    columns.extend(['Pileup__nom','Pileup__up','Pileup__down','Pdfweight__nom','Pdfweight__up','Pdfweight__down','ISR__up','ISR__down','FSR__up','FSR__down'])
	    if 'NMSSM' not in self.setname: # QCD scale variations
		columns.extend(['QCDscale_factorization__nom','QCDscale_factorization__up','QCDscale_factorization__down'])
		columns.extend(['QCDscale_renormalization__nom','QCDscale_renormalization__up','QCDscale_renormalization__down'])
		columns.extend(['QCDscale_combined__nom','QCDscale_combined__up','QCDscale_combined__down'])
	    if self.year == '16' or self.year == '17' or 'APV' in self.year:
		#columns.extend(['Prefire__nom','Prefire__up','Prefire__down'])
		columns.extend(['L1PreFiringWeight_Nom', 'L1PreFiringWeight_Up', 'L1PreFiringWeight_Dn'])	# these are the default columns in NanoAODv9
		columns.extend(['L1PreFiringWeight__nom','L1PreFiringWeight__up','L1PreFiringWeight__down'])    # these are the weight columns created by the BranchCorrection module
	    elif self.year == '18':
		columns.append('HEM_drop__nom')
            
        # get ready to send out snapshot
        #self.a.SetActiveNode(node)
        self.a.Snapshot(columns, 'HWWsnapshot_{}_{}_{}of{}.root'.format(self.setname,self.year,self.ijob,self.njobs),'Events', openOption='RECREATE',saveRunChain=True)
        self.a.SetActiveNode(startNode)
        
    # xsecs from JSON config file
    def GetXsecScale(self):	
	lumi = self.config['lumi{}'.format(self.year)]
	xsec = self.config['XSECS'][self.setname]
	if self.a.genEventSumw == 0:
	    raise ValueError('{} {}: genEventSumw is 0'.format(self.setname, self.year))
        print('Normalizing by lumi*xsec/genEventSumw:\n\t{} * {} / {} = {}'.format(lumi,xsec,self.a.genEventSumw,lumi*xsec/self.a.genEventSumw))
        return lumi*xsec/self.a.genEventSumw

    # N-1 group - this returns a dict of nodes, where each node is such that it has all but one of the cuts applied. 
    # used in order to see the effect of varying the tagger on selection
    def GetNminus1Group(self,tagger):
	cutgroup = CutGroup('taggingVars')
	# inside the studies code, we'll have made SubCollections called Higgs, LeadW, SubleadW
	# first, cuts based on softdrop mass
	cutgroup.Add('mH_{}_cut'.format(tagger),'Higgs_msoftdrop > {0} && Higgs_msoftdrop < {1}'.format(*self.cuts['mh']))
	cutgroup.Add('mLeadW_{}_cut'.format(tagger),'W1_msoftdrop > {0} && W1_msoftdrop < {1}'.format(*self.cuts['mw']))
	cutgroup.Add('mSubleadW_{}_cut'.format(tagger),'W2_msoftdrop > {0} && W2_msoftdrop < {1}'.format(*self.cuts['mw']))
	# now, cuts based on particleNet scores (for now, don't use mass-decorrelated)
	# taggers are: particleNet_HbbvsQCD, particleNet_WvsQCD
	cutgroup.Add('{}_H_cut'.format(tagger),'Higgs_{0}_HbbvsQCD > {1}'.format(tagger, self.cuts[tagger+'_HbbvsQCD']))
	cutgroup.Add('{}_LeadW_cut'.format(tagger),'W1_{0}_WvsQCD > {1}'.format(tagger, self.cuts[tagger+'_WvsQCD']))
	cutgroup.Add('{}_SubleadW_cut'.format(tagger),'W2_{0}_WvsQCD > {1}'.format(tagger, self.cuts[tagger+'_WvsQCD']))
	return cutgroup

    # N-2 group - in this case we want to plot the Higgs tag cut after *all* cuts are made EXCEPT for the Higgs mass cut
    def GetNminus2Group(self,tagger):
	cutgroup = CutGroup('taggingVars')
	# we want to add every cut EXCEPT for higgs mass cut. Starting with mass cuts:
	cutgroup.Add('mLeadW_{}_cut'.format(tagger),'W1_msoftdrop > {0} && W1_msoftdrop < {1}'.format(*self.cuts['mw']))
        cutgroup.Add('mSubleadW_{}_cut'.format(tagger),'W2_msoftdrop > {0} && W2_msoftdrop < {1}'.format(*self.cuts['mw']))
	# now we want to make cuts on particleNet scores (including Higgs tagger score)
	# after we call this function, we will grab the key that ends with 'H_cut'
        cutgroup.Add('{}_H_cut'.format(tagger),'Higgs_{0}_HbbvsQCD > {1}'.format(tagger, self.cuts[tagger+'_HbbvsQCD']))
        cutgroup.Add('{}_LeadW_cut'.format(tagger),'W1_{0}_WvsQCD > {1}'.format(tagger, self.cuts[tagger+'_WvsQCD']))
        cutgroup.Add('{}_SubleadW_cut'.format(tagger),'W2_{0}_WvsQCD > {1}'.format(tagger, self.cuts[tagger+'_WvsQCD']))
	return cutgroup



    # ------------------------------------------------------------- For selection -------------------------------------------------------------------------
    def ApplyWPick_Signal(self, WTagger, HTagger, pt, WScoreCut, eff0, eff1, eff2, year, WVariation, invert, WMass='', massWindow=[]):
	''' For use in selection - picks the 2 W jets from the 3 candidate jets after performing jet-by-jet updating of W tag status according to SF and pT
	Args:
	    WTagger    (str): The name of the original W tag branch in the DF ('Trijet_particleNetMD_WvsQCD')
	    HTagger    (str): The name of the original H tag branch in the DF ('Trijet_particleNetMD_HbbvsQCD')
	    pt         (str): The name of the corrected pT branch ('Trijet_pt_corr')
	    WScoreCut  (str): Value on which to cut on W tag (0.8)
	    effX     (float): Value of the W tagging efficiencies for the three cand. jets (X=0,1,2)
	    year       (str): 16, 16APV, 17, 18
	    WVariation (int): 0: nominal, 1: up, 2: down
	    invert    (bool): True if CR, False if SR
	    WMass      (str): Name of the column containing the (corrected) mass
	    massWindow [float,float]: lower and upper bounds on W mass window requirement. If empty list, no such requirement is made
	'''
	objIdxs = 'ObjIdxs_{}{}{}'.format('Not' if invert else '', WTagger,'_WMassWindow' if massWindow else '_noWMassWindow')
	if objIdxs not in [str(cname) for cname in self.a.DataFrame.GetColumnNames()]:
	    if massWindow:
		self.a.Define(objIdxs, 'PickWWithSFs_massWindow(%s, %s, %s, {0, 1, 2}, %s, {%f, %f}, %f, %f, %f, %f, "20%s", %i, %s)'%(
								WTagger, HTagger, pt,
								WMass, massWindow[0], massWindow[1], 
								WScoreCut,
								eff0, eff1, eff2,
								year, WVariation,
								'true' if invert else 'false'))
	    else:
	    	self.a.Define(objIdxs, 'PickWWithSFs(%s, %s, %s, {0, 1, 2}, %f, %f, %f, %f, "20%s", %i, %s)'%(WTagger, HTagger, pt, WScoreCut, eff0, eff1, eff2, year, WVariation, 'true' if invert else 'false'))
	    # At this point, we'll have a column named ObjIdxs_(NOT)_particleNetMD_WvsQCD containing the indices of 
	    # which of the three jets are the Ws and the Higgs (W1_idx, W2_idx, H_idx). Or {-1, -1, -1} if two jets didn't pass W tagging
	    self.a.Define('w1Idx','{}[0]'.format(objIdxs))
            self.a.Define('w2Idx','{}[1]'.format(objIdxs))
            self.a.Define('hIdx', '{}[2]'.format(objIdxs))
	
	#DEBUG (next 2 lines)
	nTot = self.a.DataFrame.Sum("genWeight").GetValue()
	print('NTot before WPick (signal) = {}'.format(nTot))
	self.a.Cut('Has2Ws','(w1Idx > -1) && (w2Idx > -1)')		# cut to ensure the event has the two requisite Ws
        #DEBUG (next 2 lines)
        nTot = self.a.DataFrame.Sum("genWeight").GetValue()
        print('NTot after WPick (signal) = {}'.format(nTot))

	# at this point, rename Trijet -> W1/W2/Higgs based on its index determined above
	self.a.ObjectFromCollection('W1','Trijet','w1Idx')#,skip=['msoftdrop_corrH'])
        self.a.ObjectFromCollection('W2','Trijet','w2Idx')#,skip=['msoftdrop_corrH'])
        self.a.ObjectFromCollection('H','Trijet','hIdx')#,skip=['msoftdrop_corrH'])

	'''
	# Now add the W mass window cut, if applicable (only use regressed mass, since reg/SD are mostly compatible in this range)
	if massCut and not invert: # only do this in SR
	    print('Applying W-mass window cut b/w [{0},{1}] GeV'.format(*massCut))
	    self.a.Cut('W1_massCut','W1_mregressed_corr > {0} && W1_mregressed_corr < {1}'.format(*massCut))
	    self.a.Cut('W2_massCut','W2_mregressed_corr > {0} && W2_mregressed_corr < {1}'.format(*massCut))
	'''

        # Cutflow info
        if (invert == True):
            self.nWTag_CR = self.getNweighted()
            self.AddCutflowColumn(self.nWTag_CR, 'nWTag_CR')
        else:
            if not massWindow:
                self.nWTag_SR = self.getNweighted()
                self.AddCutflowColumn(self.nWTag_SR, 'nWTag_SR')
            else:
                self.nWTag_SR_massWindow = self.getNweighted()
                self.AddCutflowColumn(self.nWTag_SR_massWindow, 'nWTag_SR_massWindow')

	# in order to avoid column naming duplicates, call these LeadW, SubleadW, Higgs
	self.a.Define('LeadW_vect_softdrop','hardware::TLvector(W1_pt_corr, W1_eta, W1_phi, W1_msoftdrop_corr)')
	self.a.Define('SubleadW_vect_softdrop','hardware::TLvector(W2_pt_corr, W2_eta, W2_phi, W2_msoftdrop_corr)')
	self.a.Define('Higgs_vect_softdrop','hardware::TLvector(H_pt_corr, H_eta, H_phi, H_msoftdrop_corr)')
	# ------- regressed mass --------------
        self.a.Define('LeadW_vect_regressed','hardware::TLvector(W1_pt_corr, W1_eta, W1_phi, W1_mregressed_corr)')
        self.a.Define('SubleadW_vect_regressed','hardware::TLvector(W2_pt_corr, W2_eta, W2_phi, W2_mregressed_corr)')
        self.a.Define('Higgs_vect_regressed','hardware::TLvector(H_pt_corr, H_eta, H_phi, H_mregressed_corr)')
	# make X and Y mass for both softdrop and regressed masses
	self.a.Define('mhww_softdrop','hardware::InvariantMass({LeadW_vect_softdrop,SubleadW_vect_softdrop,Higgs_vect_softdrop})')
	self.a.Define('mww_softdrop','hardware::InvariantMass({LeadW_vect_softdrop,SubleadW_vect_softdrop})')
        self.a.Define('mhww_regressed','hardware::InvariantMass({LeadW_vect_regressed, SubleadW_vect_regressed, Higgs_vect_regressed})')
        self.a.Define('mww_regressed','hardware::InvariantMass({LeadW_vect_regressed,SubleadW_vect_regressed})')

	return self.a.GetActiveNode()

    def ApplyWPick(self, tagger, invert, WMass='', massWindow=[]):
	'''For use in selection with all non-signal samples
	Args:
	    tagger (str): The name of the original W tag branch in the DF ('Trijet_particleNetMD_WvsQCD')
	    invert (bool): True if CR, False if SR
	    massWindow [float,float]: lower and upper bounds on W mass window requirement. If empty list, no requirement is made
	'''
	objIdxs = 'ObjIdxs_{}{}{}'.format('Not' if invert else '', tagger, '_WMassWindow' if massWindow else '_noWMassWindow')
	if objIdxs not in [str(cname) for cname in self.a.DataFrame.GetColumnNames()]:
	    # first option is tagger, second is W score cut threshold (0.8), third is invert boolean
	    if massWindow:
		self.a.Define(objIdxs,'PickW_massWindow(%s, {0, 1, 2}, {%f, %f}, %s, %s, %s)'%(tagger,massWindow[0], massWindow[1], WMass, 0.8, 'true' if invert else 'false'))
	    else:
		self.a.Define(objIdxs,'PickW(%s, {0, 1, 2}, %s, %s)'%(tagger, 0.8, 'true' if invert else 'false'))
            self.a.Define('w1Idx','{}[0]'.format(objIdxs))
            self.a.Define('w2Idx','{}[1]'.format(objIdxs))
            self.a.Define('hIdx', '{}[2]'.format(objIdxs))
	self.a.Cut('Has2Ws','w1Idx > -1 && w2Idx > -1')
	# make collections
        self.a.ObjectFromCollection('W1','Trijet','w1Idx')
        self.a.ObjectFromCollection('W2','Trijet','w2Idx')
        self.a.ObjectFromCollection('H','Trijet','hIdx')
	'''
	# add mass window cut, if applicable
	if massCut and not invert:
	    print('Applying W-mass window cut b/w [{0},{1}] GeV'.format(*massCut))
            self.a.Cut('W1_massCut','W1_mregressed_corr > {0} && W1_mregressed_corr < {1}'.format(*massCut))
            self.a.Cut('W2_massCut','W2_mregressed_corr > {0} && W2_mregressed_corr < {1}'.format(*massCut))
	'''
        # Cutflow info
        if (invert == True):
            self.nWTag_CR = self.getNweighted()
            self.AddCutflowColumn(self.nWTag_CR, 'nWTag_CR')
        else:
            if not massWindow:
                self.nWTag_SR = self.getNweighted()
                self.AddCutflowColumn(self.nWTag_SR, 'nWTag_SR')
            else:
                self.nWTag_SR_massWindow = self.getNweighted()
                self.AddCutflowColumn(self.nWTag_SR_massWindow, 'nWTag_SR_massWindow')
	# softdrop mass
        self.a.Define('LeadW_vect_softdrop','hardware::TLvector(W1_pt_corr, W1_eta, W1_phi, W1_msoftdrop_corr)')
        self.a.Define('SubleadW_vect_softdrop','hardware::TLvector(W2_pt_corr, W2_eta, W2_phi, W2_msoftdrop_corr)')
        self.a.Define('Higgs_vect_softdrop','hardware::TLvector(H_pt_corr, H_eta, H_phi, H_msoftdrop_corr)')
	# regressed mass
        self.a.Define('LeadW_vect_regressed','hardware::TLvector(W1_pt_corr, W1_eta, W1_phi, W1_mregressed_corr)')
        self.a.Define('SubleadW_vect_regressed','hardware::TLvector(W2_pt_corr, W2_eta, W2_phi, W2_mregressed_corr)')
        self.a.Define('Higgs_vect_regressed','hardware::TLvector(H_pt_corr, H_eta, H_phi, H_mregressed_corr)')
	# X and Y masses for both softdrop and regressed mass
        self.a.Define('mhww_softdrop','hardware::InvariantMass({LeadW_vect_softdrop,SubleadW_vect_softdrop,Higgs_vect_softdrop})')
        self.a.Define('mww_softdrop','hardware::InvariantMass({LeadW_vect_softdrop,SubleadW_vect_softdrop})')
        self.a.Define('mhww_regressed','hardware::InvariantMass({LeadW_vect_regressed, SubleadW_vect_regressed, Higgs_vect_regressed})')
        self.a.Define('mww_regressed','hardware::InvariantMass({LeadW_vect_regressed,SubleadW_vect_regressed})')

        return self.a.GetActiveNode()







    # ------------------------------------------------------------- DEPRECATED -------------------------------------------------------------------------
    # for comparing mX vs mY
    # DEPRECATED - ONLY FOR USE IN STUDIES
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
        region1.Add('MXvsMY_mH_{}_cut'.format(tagger),'Higgs_msoftdrop > {0} && Higgs_msoftdrop < {1}'.format(*self.cuts['mh']))
        region1.Add('MXvsMY_mLeadW_{}_cut'.format(tagger),'W1_msoftdrop > {0} && W1_msoftdrop < {1}'.format(*self.cuts['mw']))
        region1.Add('MXvsMY_mSubleadW_{}_cut'.format(tagger),'W2_msoftdrop > {0} && W2_msoftdrop < {1}'.format(*self.cuts['mw']))
	if (len(Hbb) > len(W)):    # we are using tight W cut 	- AKA SIGNAL REGION
            # W score cuts 
            region1.Add('MXvsMY_{}_LeadW_cut'.format(tagger),'W1_{0}_WvsQCD > {1}'.format(tagger, W[0])) 
            region1.Add('MXvsMY_{}_SubleadW_cut'.format(tagger),'W2_{0}_WvsQCD > {1}'.format(tagger, W[0]))
	    # H score in the specified region
	    region1.Add('MXvsMY_{}_H_cut'.format(tagger),'Higgs_{0}_HbbvsQCD < {1}'.format(tagger, Hbb[0])) 
        else:		# we are using loose W cut, in a region W[0] < WvsQCD < W[1]	- AKA CONTROL REGION
            region1.Add('MXvsMY_{}_LeadW_cut'.format(tagger),'W1_{0}_WvsQCD > {1} && W1_{0}_WvsQCD < {2}'.format(tagger, W[0], W[1]))
            region1.Add('MXvsMY_{}_SubleadW_cut'.format(tagger),'W2_{0}_WvsQCD > {1} && W2_{0}_WvsQCD < {2}'.format(tagger, W[0], W[1]))
            region1.Add('MXvsMY_{}_H_cut'.format(tagger),'Higgs_{0}_HbbvsQCD < {1}'.format(tagger, Hbb[0]))

	# every cut, but Hbb[0] < Hbb < Hbb[1]
	# --------------------------------------------
	# 		Higgs Loose
	# --------------------------------------------
	region2 = CutGroup('region2')
        region2.Add('MXvsMY_mH_{}_cut'.format(tagger),'Higgs_msoftdrop > {0} && Higgs_msoftdrop < {1}'.format(*self.cuts['mh']))
	region2.Add('MXvsMY_mLeadW_{}_cut'.format(tagger),'W1_msoftdrop > {0} && W1_msoftdrop < {1}'.format(*self.cuts['mw']))
	region2.Add('MXvsMY_mSubleadW_{}_cut'.format(tagger),'W2_msoftdrop > {0} && W2_msoftdrop < {1}'.format(*self.cuts['mw']))
	if (len(Hbb) > len(W)):
            region2.Add('MXvsMY_{}_LeadW_cut'.format(tagger),'W1_{0}_WvsQCD > {1}'.format(tagger, W[0]))
            region2.Add('MXvsMY_{}_SubleadW_cut'.format(tagger),'W2_{0}_WvsQCD > {1}'.format(tagger, W[0]))
            region2.Add('MXvsMY_{}_H_cut'.format(tagger),'Higgs_{0}_HbbvsQCD > {1} && Higgs_{0}_HbbvsQCD < {2}'.format(tagger, Hbb[0], Hbb[1]))
	else:
            region2.Add('MXvsMY_{}_LeadW_cut'.format(tagger),'W1_{0}_WvsQCD > {1} && W1_{0}_WvsQCD < {2}'.format(tagger, W[0], W[1]))
            region2.Add('MXvsMY_{}_SubleadW_cut'.format(tagger),'W2_{0}_WvsQCD > {1} && W2_{0}_WvsQCD < {2}'.format(tagger, W[0], W[1]))
            region2.Add('MXvsMY_{}_H_cut'.format(tagger),'Higgs_{0}_HbbvsQCD > {1} && Higgs_{0}_HbbvsQCD < {2}'.format(tagger, Hbb[0], Hbb[1]))

	# every cut but Hbb > Hbb[1]
	# -----------------------------------------------
	# 		Higgs Pass
	# -----------------------------------------------
	region3 = CutGroup('region3')
        region3.Add('MXvsMY_mH_{}_cut'.format(tagger),'Higgs_msoftdrop > {0} && Higgs_msoftdrop < {1}'.format(*self.cuts['mh']))
	region3.Add('MXvsMY_mLeadW_{}_cut'.format(tagger),'W1_msoftdrop > {0} && W1_msoftdrop < {1}'.format(*self.cuts['mw']))
	region3.Add('MXvsMY_mSubleadW_{}_cut'.format(tagger),'W2_msoftdrop > {0} && W2_msoftdrop < {1}'.format(*self.cuts['mw']))
	if (len(Hbb) > len(W)):
	    region3.Add('MXvsMY_{}_LeadW_cut'.format(tagger),'W1_{0}_WvsQCD > {1}'.format(tagger, W[0]))
	    region3.Add('MXvsMY_{}_SubleadW_cut'.format(tagger),'W2_{0}_WvsQCD > {1}'.format(tagger, W[0]))
	    region3.Add('MXvsMY_{}_H_cut'.format(tagger),'Higgs_{0}_HbbvsQCD > {1}'.format(tagger, Hbb[1]))
	else:
	    region3.Add('MXvsMY_{}_LeadW_cut'.format(tagger),'W1_{0}_WvsQCD > {1} && W1_{0}_WvsQCD < {2}'.format(tagger, W[0], W[1]))
	    region3.Add('MXvsMY_{}_SubleadW_cut'.format(tagger),'W2_{0}_WvsQCD > {1} && W2_{0}_WvsQCD < {2}'.format(tagger, W[0], W[1]))
	    region3.Add('MXvsMY_{}_H_cut'.format(tagger),'Higgs_{0}_HbbvsQCD > {1}'.format(tagger, Hbb[1]))
	
	# return list (fixed order) of the three cutgroups, for use in XHYbbWW_studies.py
	return [region1, region2, region3]


    def ApplyMassCuts(self):
	# perform Higgs mass window cut, save cutflow info
	self.a.Cut('mH_{}_cut'.format('window'),'Higgs_msoftdrop > {0} && Higgs_msoftdrop < {1}'.format(*self.cuts['mh']))
	self.nHiggs = self.getNweighted()
	self.AddCutflowColumn(self.nHiggs, 'nHiggsMassCut')
	# Lead W mass window cut, cutflow
	self.a.Cut('mLeadW_{}_cut'.format('window'),'LeadW_msoftdrop > {0} && LeadW_msoftdrop < {1}'.format(*self.cuts['mw']))
	self.nLeadW = self.getNweighted()
	self.AddCutflowColumn(self.nLeadW, 'nLeadWMassCut')
	# sublead W
	self.a.Cut('mSubleadW_{}_cut'.format('window'),'SubleadW_msoftdrop > {0} && SubleadW_msoftdrop > {1}'.format(*self.cuts['mw']))
	self.nSubleadW = self.getNweighted()
	self.AddCutflowColumn(self.nSubleadW, 'nSubleadWMassCut')
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
	    # Signal region - ID two W jets
	    self.a.Cut('LeadW_{}_cut_{}'.format(tagger,SRorCR), 'LeadW_{0} > {1}'.format(tagger,W_SR))
	    self.a.Cut('SubleadW_{}_cut_{}'.format(tagger,SRorCR), 'SubleadW_{0} > {1}'.format(tagger,W_SR))
	else:
	    # Control Region - invert top IDs
	    self.a.Cut('LeadW_{}_cut_{}'.format(tagger,SRorCR), 'LeadW_{0} > {1} && LeadW_{0} < {2}'.format(tagger,*W_CR))
	    self.a.Cut('SubleadW_{}_cut_{}'.format(tagger,SRorCR), 'SubleadW_{0} > {1} && SubleadW_{0} < {2}'.format(tagger,*W_CR))
	# save cutflow info
	self.nWTag = self.getNweighted()
	self.AddCutflowColumn(self.nWTag, 'nWTag_{}'.format(SRorCR))
	return self.a.GetActiveNode()

    def ApplyHiggsTag(self, SRorCR, tagger, signal, WMassCut=False):
	'''
	Fail:	H < 0.8
	Loose:	0.8 < H < 0.98
	Pass: 	H > 0.98

	if signal:
	Fail:   NewTagCats==0
	Loose:  NewTagCats==1
	Pass:	NewTagCats==2
	'''
	assert(SRorCR=='SR' or SRorCR=='CR')
	print('ApplyHiggsTag(): Using H tagger {}'.format(tagger))
	checkpoint = self.a.GetActiveNode()
	cuts = [0.8, 0.98]
	FLP = {}
	# Higgs fail + cutflow info 
	# FAIL NO LONGER USED IN ANALYSIS, BUT KEEP IT ANYWAY
	FLP['fail'] = self.a.Cut('HbbTag_fail','{0} < {1}'.format(tagger, cuts[0]) if not signal else 'NewTagCats==0')
	if SRorCR=='SR':
	    self.nHF_SR = self.getNweighted()
	    self.AddCutflowColumn(self.nHF_SR, 'higgsF_SR')
	else:
	    self.nHF_CR = self.getNweighted()
	    self.AddCutflowColumn(self.nHF_CR, 'higgsF_CR')

	# Higgs Loose + cutflow
	self.a.SetActiveNode(checkpoint)
	FLP['loose'] = self.a.Cut('HbbTag_loose','{0} > {1} && {0} < {2}'.format(tagger, *cuts) if not signal else 'NewTagCats==1')
	if SRorCR == 'SR':
	    self.nHL_SR = self.getNweighted()
	    self.AddCutflowColumn(self.nHL_SR, 'higgsL_SR')
	else:
	    self.nHL_CR = self.getNweighted()
	    self.AddCutflowColumn(self.nHL_CR, 'higgsL_CR')

	# Higgs Pass + cutflow
	self.a.SetActiveNode(checkpoint)
	FLP['pass'] = self.a.Cut('HbbTag_pass','{0} > {1}'.format(tagger, cuts[1]) if not signal else 'NewTagCats==2')
	if SRorCR == 'SR':
	    self.nHP_SR = self.getNweighted()
	    self.AddCutflowColumn(self.nHP_SR, 'higgsP_SR')
	else:
	    self.nHP_CR = self.getNweighted()
	    self.AddCutflowColumn(self.nHP_CR, 'higgsP_CR')

	# ---------- Now do the same but with a regressed mass cut on the H jet ---------------------------
	mreg = 'H_mregressed_corr'
	mreg_cut_SR = '{0} >= 110 && {0} < 145'.format(mreg)
	mreg_cut_CR = '(({0} >= 92.5 && {0} < 110) || ({0} >= 145 && {0} < 162))'.format(mreg)
	#mreg_cut_CR = '{0} >= 92.5 && {0} < 110 || {0} >= 145 && {0} < 162'.format(mreg)

        # Higgs Loose + mreg cut + cutflow
        self.a.SetActiveNode(checkpoint)
	loose_cut_mreg = '{0} > {1} && {0} < {2}'.format(tagger, *cuts) if not signal else 'NewTagCats==1'
        self.a.Cut('HbbTag_loose_temp', loose_cut_mreg)
        print('number after temp cut: {}'.format(self.getNweighted()))
        FLP['loose_mHreg_cut'] = self.a.Cut('HbbTag_loose_mreg', mreg_cut_SR if SRorCR == 'SR' else mreg_cut_CR)
        if SRorCR == 'SR':
	    if WMassCut:
		self.nHL_SR_mreg_WMass = self.getNweighted()
		self.AddCutflowColumn(self.nHL_SR_mreg_WMass, 'higgsL_SR_mHreg_mWreg')
	    else:
            	self.nHL_SR_mreg = self.getNweighted()
            	self.AddCutflowColumn(self.nHL_SR_mreg, 'higgsL_SR_mHreg')
        else:
            self.nHL_CR_mreg = self.getNweighted()
            self.AddCutflowColumn(self.nHL_CR_mreg, 'higgsL_CR_mHreg')

        # Higgs Pass + mreg cut + cutflow
        self.a.SetActiveNode(checkpoint)
	pass_cut_mreg = '{0} > {1}'.format(tagger, cuts[1]) if not signal else 'NewTagCats==2'
        self.a.Cut('HbbTag_pass_temp', pass_cut_mreg)
	print('number after temp cut: {}'.format(self.getNweighted()))
        FLP['pass_mHreg_cut'] = self.a.Cut('HbbTag_pass_mreg', mreg_cut_SR if SRorCR == 'SR' else mreg_cut_CR)
        if SRorCR == 'SR':
	    if WMassCut:
            	self.nHP_SR_mreg_WMass = self.getNweighted()
            	self.AddCutflowColumn(self.nHP_SR_mreg_WMass, 'higgsP_SR_mHreg_mWreg')
	    else:
                self.nHP_SR_mreg = self.getNweighted()
                self.AddCutflowColumn(self.nHP_SR_mreg, 'higgsP_SR_mHreg')
        else:
            self.nHP_CR_mreg = self.getNweighted()
            self.AddCutflowColumn(self.nHP_CR_mreg, 'higgsP_CR_mHreg')

	# reset state, return dict
	self.a.SetActiveNode(checkpoint)
	return FLP
    # ------------------------------------------------------------------------------------------------------------------------------------------------

# for use in selection - essentially just creates combinations of all the JME variations
def JMEvariationStr(p, variation):
    '''Perform the calibration for both softdrop and regressed masses
    The AutoJME function has been modified to rename JMX -> JMX_regressed/JMX_softdrop
    '''
    base_calibs = ['Trijet_JES_nom','Trijet_JER_nom','Trijet_JMS_nom','Trijet_JMR_nom']
    variationType = variation.split('_')[0]
    jmr_variation = variation.split('_')
    pt_calib_vect = '{'
    softdrop_mass_calib_vect = '{'
    regressed_mass_calib_vect = '{'
    for c in base_calibs:
        if 'JM' in c and p != 'Top':
            for mass in ['softdrop','regressed']:
                modifier = '_%s_'%(mass)
                if variationType in c:
                    modifier = modifier.join(jmr_variation)
                else:
                    modifier = 'JM%s'%('S' if variationType == 'JMR' else 'R')+modifier+'nom'
                if mass == 'softdrop':
                    softdrop_mass_calib_vect += '%s,'%('Trijet_'+modifier)
                else:
                    regressed_mass_calib_vect += '%s,'%('Trijet_'+modifier)
        elif 'JE' in c:
            pt_calib_vect += '%s,'%('Trijet_'+variation if variationType in c else c)
            regressed_mass_calib_vect += '%s,'%('Trijet_'+variation if variationType in c else c)
            softdrop_mass_calib_vect += '%s,'%('Trijet_'+variation if variationType in c else c)

    pt_calib_vect = pt_calib_vect[:-1]+'}'
    regressed_mass_calib_vect = regressed_mass_calib_vect[:-1]+'}'
    softdrop_mass_calib_vect = softdrop_mass_calib_vect[:-1]+'}'
    return pt_calib_vect, softdrop_mass_calib_vect, regressed_mass_calib_vect
