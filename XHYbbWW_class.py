import ROOT
from TIMBER.Analyzer import Correction, CutGroup, ModuleWorker, analyzer
from TIMBER.Tools.Common import CompileCpp, OpenJSON
from TIMBER.Tools.AutoPU import ApplyPU
from JMEvalsOnly import JMEvalsOnly
from collections import OrderedDict
import TIMBER.Tools.AutoJME as AutoJME
#from memory_profiler import profile

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
            return self.a.DataFrame.Sum("genWeight")
        else:
            return self.a.DataFrame.Count()

    # for creating snapshots
    def ApplyKinematicsSnap(self):
        self.NPROC = self.getNweighted()
        #self.AddCutflowColumn(self.NPROC, "NPROC")
     
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
        #self.AddCutflowColumn(self.NFLAGS, "NFLAGS")

        self.a.Cut('FatJet_cut', 'nFatJet > 2')     # we want at least 3 fatJets
        self.NJETS = self.getNweighted()
        #self.AddCutflowColumn(self.NJETS, "NJETS")

        self.a.Cut('pt_cut', 'FatJet_pt[0] > 400 && FatJet_pt[1] > 200 && FatJet_pt[2] > 200')      # jets ordered by pt
        self.NPT = self.getNweighted()
        #self.AddCutflowColumn(self.NPT, "NPT")

        self.a.Cut('eta_cut', 'abs(FatJet_eta[0]) < 2.4 && abs(FatJet_eta[1]) < 2.4 && abs(FatJet_eta[2]) < 2.4')   # no super forward jets
        self.NETA = self.getNweighted()
        #self.AddCutflowColumn(self.NETA, "NETA")

        self.a.Cut('msoftdrop_cut','FatJet_msoftdrop[0] > 50 && FatJet_msoftdrop[1] > 40 && FatJet_msoftdrop[2] > 40') # should always use softdrop mass
        self.NMSD = self.getNweighted()
        #self.AddCutflowColumn(self.NMSD, "NMSD")

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
    #@profile
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
                # For some reason, diboson processes don't have the LHEScaleWeight branch, so don't apply to those either.
                if ('NMSSM' not in self.setname) and (('WW' not in self.setname) and ('WZ' not in self.setname) and ('ZZ' not in self.setname)):
                    # First instatiate a correction module for the factorization correction
                    facCorr = Correction('QCDscale_factorization','LHEScaleWeights.cc',corrtype='weight',mainFunc='evalFactorization')
                    self.a.AddCorrection(facCorr, evalArgs={'LHEScaleWeights':'LHEScaleWeight'})
                    # Now clone it and call evalRenormalization for the renormalization correction
                    renormCorr = facCorr.Clone('QCDscale_renormalization',newMainFunc='evalRenormalization',newType='weight')
                    self.a.AddCorrection(renormCorr, evalArgs={'LHEScaleWeights':'LHEScaleWeight'})
                    # Now do one for the combined correction
                    combCorr = facCorr.Clone('QCDscale_combined',newMainFunc='evalCombined',newType='weight')
                    self.a.AddCorrection(combCorr, evalArgs={'LHEScaleWeights':'LHEScaleWeight'})
                    # And finally, do one for the uncertainty
                    # See: https://indico.cern.ch/event/938672/contributions/3943718/attachments/2073936/3482265/MC_ContactReport_v3.pdf (slide 27)
                    QCDScaleUncert = facCorr.Clone('QCDscale_uncert',newMainFunc='evalUncert',newType='uncert')
                    self.a.AddCorrection(QCDScaleUncert, evalArgs={'LHEScaleWeights':'LHEScaleWeight'})

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
                # I forgot to add the `genW` branch in snapshots, so just redo it here...
                # In the end it doesn't really matter, since the correction just uses genWeight.
                # One could also opt to add genWeight*GetXsecScale() in the MakeWeightCols() call as well..
                # This is EXTREMELY IMPORTANT for getting the event weighting correct
                genWCorr = Correction('genW','TIMBER/Framework/TopPhi_modules/BranchCorrection.cc',corrtype='corr',mainFunc='evalCorrection')
                #self.a.AddCorrection(Correction('genW',corrtype='corr'))
                self.a.AddCorrection(genWCorr, evalArgs={'val':'genWeight'})

                self.a.AddCorrection(Correction('Pileup',corrtype='weight'))
                self.a.AddCorrection(Correction('ISRunc',corrtype='uncert'))
                self.a.AddCorrection(Correction('FSRunc',corrtype='uncert'))
                if self.a.lhaid != -1: self.a.AddCorrection(Correction('Pdfweight',corrtype='uncert'))
                if 'NMSSM' not in self.setname:
                    # perhaps the first three should be uncert types, but because nominal = 1.0, it's functionally equivalent
                    self.a.AddCorrection(Correction('QCDscale_factorization',corrtype='weight'))
                    self.a.AddCorrection(Correction('QCDscale_renormalization',corrtype='weight'))
                    self.a.AddCorrection(Correction('QCDscale_combined',corrtype='weight'))
                    self.a.AddCorrection(Correction('QCDscale_uncert',corrtype='uncert'))
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
            # use the values before H/W/W identification (aka the 'trig' values)
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
            #'jet0','jet1','jet2','dR01','dR02','dR12',
            'NPROC', 'NJETS', 'NPT', 'NETA', 'NMSD'
        ]
        
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
            columns.extend(['QCDscale_uncert__up','QCDscale_uncert__down'])
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
        lumi = self.config['lumi%s'%self.year]
        xsec = self.config['XSECS'][self.setname]
        if self.a.genEventSumw == 0:
            raise ValueError('{} {}: genEventSumw is 0'.format(self.setname, self.year))
        print('Normalizing by lumi*xsec/genEventSumw:\n\t{} * {} / {} = {}'.format(lumi,xsec,self.a.genEventSumw,lumi*xsec/self.a.genEventSumw))
        return lumi*xsec/self.a.genEventSumw


    #####################################################################################
    #					SELECTION METHODS				                                #
    #-----------------------------------------------------------------------------------#
    # Selection consists of first picking the two W candidates (if signal region) and   #
    # then picking the Higgs candidate via progressively tightening cuts on the Higgs   #
    # candidate jet's particleNetMD_HbbvsQCD score.				                    	#
    # This must be done separately for ttbar, signal, and data samples. The signal is   #
    # subject to the Wqq/Hbb scale factors, ttbar is subject to the mistagging scale    #
    # factors, and the data is subject to neither. The following two methods are meant  #
    # to handle each of the cases separately.                                           #
    #####################################################################################
    #@profile
    def Pick_W_candidates(
        self,
        SRorCR              = 'SR',                         # whether in SR or CR for cutflow
        WqqSFHandler_obj    = 'WqqSFHandler',               # instance of the Wqq SF handler class
        Wqq_discriminant    = 'Trijet_particleNetMD_WvsQCD',# raw MD_WvsQCD tagger score from PNet
        corrected_pt	    = 'Trijet_pt_corr',		        # corrected pt
        trijet_eta	        = 'Trijet_eta',			        # eta
        corrected_mass	    = 'Trijet_mregressed_corr',		# corrected softdrop mass for mass window req
        genMatchCats	    = 'Trijet_GenMatchCats',		# gen matching jet cats from `TopMergingFunctions.cc`
        Wqq_variation	    = 0,				            # 0: nominal, 1: up, 2:down
        invert		        = False,				        # False: SR, True: CR
        mass_window	        = [60., 110]				    # w mass window for selection
    ):
        # Cutflow - before W selection
        if SRorCR == 'SR':
            self.NBEFORE_W_PICK_SR = self.getNweighted()
        else:
            self.NBEFORE_W_PICK_CR = self.getNweighted()

        # Column names for the W (anti)candidate indices
        objIdxs = 'ObjIdxs_%s'%('CR' if invert else 'SR')
        # Create the column containing the indices of the three jets after matching.
        # This is done separately for the ttbar+signal and data/otherMC
        if ('ttbar' in self.setname) or ('NMSSM' in self.setname):
            self.a.Define(objIdxs,
                '%s.Pick_W_candidates(%s, %s, %s, %s, %s, %s, %s, {%f, %f}, {0, 1, 2})'%(
                    WqqSFHandler_obj, # we are calling this instance's method
                    Wqq_discriminant,
                    corrected_pt,
                    trijet_eta,
                    corrected_mass,
                    genMatchCats,
                    Wqq_variation,
                    'true' if invert else 'false',
                    mass_window[0],
                    mass_window[1]
                )
            )
        else:
            # This assumes that `HWWmodules.cc` has been compiled already
            self.a.Define(objIdxs, 
                'Pick_W_candidates_standard(%s, %s, %s, {0, 1, 2})'%(
                    Wqq_discriminant,
                    0.8,
                    'true' if invert else 'false'
                )
            )
        # At this point, we'll have a column named ObjIdxs_SR/CR containing the indices of
        # which of the three jets are the Ws and the Higgs (W1_idx, W2_idx, H_idx). 
        # Or {-1, -1, -1} if at least two jets didn't pass W tagging
        self.a.Define('w1Idx','{}[0]'.format(objIdxs))
        self.a.Define('w2Idx','{}[1]'.format(objIdxs))
        self.a.Define('hIdx', '{}[2]'.format(objIdxs))
        self.a.Cut('Has2Ws','(w1Idx > -1) && (w2Idx > -1) && (hIdx > -1)') # cut to ensure the event has the two requisite Ws

        # Cutflow - after W selection
        if SRorCR == 'SR':
            self.NAFTER_W_PICK_SR = self.getNweighted()
        else:
            self.NAFTER_W_PICK_CR = self.getNweighted()

        # Now perform the mass window cut in the SR
        if not invert:
            # ensure both W candidates are within the mW window
            mW1 = '%s[w1Idx]'%corrected_mass
            mW2 = '%s[w2Idx]'%corrected_mass
            mWcut = '({0} >= {2}) && ({0} <= {3}) && ({1} >= {2}) && ({1} <= {3})'.format(mW1,mW2,mass_window[0],mass_window[1])
            self.a.Cut('mW_window',mWcut)
            # Cutflow - after W mass window (SR only)
            self.NAFTER_W_MASS_REQ_SR = self.getNweighted()

        # at this point, rename Trijet -> W1/W2/Higgs based on its index determined above
        cols_to_skip = ['vect_msoftdrop','vect_mregressed','vect_msoftdrop_corr','vect_mregressed_corr','tau2','tau3','tau1','tau4','particleNetMD_QCD','deepTagMD_HbbvsQCD','particleNet_TvsQCD','particleNetMD_Xcc','deepTagMD_WvsQCD','particleNet_QCD','jetId','particleNetMD_Xbb','particleNet_WvsQCD','deepTagMD_ZHbbvsQCD','deepTag_TvsQCD','rawFactor','particleNetMD_Xqq']
        cols = ['Trijet_%s'%i for i in cols_to_skip]
        self.a.ObjectFromCollection('W1','Trijet','w1Idx',skip=cols)#,skip=['msoftdrop_corrH'])
        self.a.ObjectFromCollection('W2','Trijet','w2Idx',skip=cols)#,skip=['msoftdrop_corrH'])
        self.a.ObjectFromCollection('H','Trijet','hIdx',skip=cols)#,skip=['msoftdrop_corrH'])
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

    #@#profile
    def ApplyHiggsTag(
	self,
        SRorCR              = 'SR', 
        HbbSFHandler_obj    = 'HbbSFHandler',               # instance of the Hbb SF handler class
        Hbb_discriminant    = 'H_particleNetMD_HbbvsQCD',	# raw MD_HbbvsQCD tagger score from PNet
        corrected_pt        = 'H_pt_corr',                  # corrected pt
        jet_eta 	        = 'H_eta',                      # eta
        corrected_mass      = 'H_mregressed_corr',          # corrected softdrop mass for mass window req
        genMatchCat         = 'H_GenMatchCats',             # gen matching jet cat from `TopMergingFunctions.cc`
        Hbb_variation       = 0,                            # 0: nominal, 1: up, 2:down
	invert		    = False,			            # False: SR, True: QCD CR
        mass_window         = [60., 110]                    # H mass window for selection
    ):

        # Cutflow - before Higgs selection
        if SRorCR == 'SR':
            self.NBEFORE_H_PICK_SR = self.getNweighted()
        else:
            self.NBEFORE_H_PICK_CR = self.getNweighted()

        # Create the column determining whether or not the H candidate passes the H tagger wp (0.98)
        if ('ttbar' in self.setname) or ('NMSSM' in self.setname):
            self.a.Define('HiggsTagStatus',
                '%s.GetNewHCat(%s, %s, %s, %s, %s)'%(
                    HbbSFHandler_obj,
                    Hbb_discriminant,
                    corrected_pt,
                    jet_eta,
                    Hbb_variation,
                    genMatchCat
                )
            )
        else:
            # This assumes that `HWWmodules.cc` has been compiled already
            self.a.Define('HiggsTagStatus','Pick_H_candidate_standard(%s, %s)'%(Hbb_discriminant, 0.98))

        # At this point, we have a column describing whether or not the Higgs candidate is Higgs-tagged.
        #   - For ttbar, mistagging SFs will have been applied to account for the fact that a gen top may be mistagged.
        #   - For signal, tagging SFs will have been applied to match the performance of the tagger in data.
        #   - For anything else, only the raw tagging score is used to determine tagged/not tagged.
        # We will now be able to define the Fail and Pass regions and return them.
        out = OrderedDict()
        checkpoint = self.a.GetActiveNode()
        '''
        print('DEBUG 1 ------------')
        print('\t%s: %s'%(Hbb_discriminant,self.a.DataFrame.GetColumnType(Hbb_discriminant)))
        print('\t%s: %s'%(corrected_pt,self.a.DataFrame.GetColumnType(corrected_pt)))
        print('\t%s: %s'%(jet_eta,self.a.DataFrame.GetColumnType(jet_eta)))
        print('\t%s: %s'%(genMatchCat,self.a.DataFrame.GetColumnType(genMatchCat)))

        self.a.DataFrame.Sum("genWeight").GetValue()
        '''
	# Begin loop over analysis regions
	# First, don't require Higgs mass cut:
        for region in ['fail','pass']:
            print('Performing Higgs tagging in %s of %s...'%(region, 'CR' if invert else 'SR'))
            self.a.SetActiveNode(checkpoint)
            # 0 indicates Higgs jet failed tagging, 1 indicates it passed tagging requirement
            out[region] = self.a.Cut('HbbTag_%s'%region, 'HiggsTagStatus == %s'%(0 if region == 'fail' else 1))
            #print('DEBUG %s'%region)
            #print('\t%s: %s'%('HiggsTagStatus',self.a.DataFrame.GetColumnType('HiggsTagStatus')))
            #print('End DEBUG %s'%region)
            #self.a.DataFrame.Sum("genWeight").GetValue()
            #print('test')

            # Cutflow
            if SRorCR == 'SR':
                if region == 'fail':
                    self.NAFTER_H_PICK_SR_FAIL = self.getNweighted()
                else:
                    self.NAFTER_H_PICK_SR_PASS = self.getNweighted()
            else:
                if region == 'fail':
                    self.NAFTER_H_PICK_CR_FAIL = self.getNweighted()
                else:
                    self.NAFTER_H_PICK_CR_PASS = self.getNweighted()

        # Now, do the same but require a Higgs mass window cut
        mreg_cut_SR = '{0} >= 110 && {0} < 145'.format(corrected_mass)
        mreg_cut_CR = '(({0} >= 92.5 && {0} < 110) || ({0} >= 145 && {0} < 162))'.format(corrected_mass)
        for region in ['fail_mH_window','pass_mH_window']:
            print('Performing Higgs tagging in %s of %s WITH Higgs mass window...'%(region, 'CR' if invert else 'SR'))
            self.a.SetActiveNode(checkpoint)
            self.a.Cut('HbbTag_%s_massreq_cut'%region,mreg_cut_CR if invert else mreg_cut_SR) # perform the mass requirement
            out[region] = self.a.Cut('HbbTag_%s'%region, 'HiggsTagStatus == %s'%(0 if 'fail' in region else 1))
            if SRorCR == 'SR':
                if 'fail' in region:
                    self.NAFTER_H_PICK_SR_FAIL_MHCUT = self.getNweighted()
                else:
                    self.NAFTER_H_PICK_SR_PASS_MHCUT = self.getNweighted()
            else:
                if 'fail' in region:
                    self.NAFTER_H_PICK_CR_FAIL_MHCUT = self.getNweighted()
                else:
                    self.NAFTER_H_PICK_CR_PASS_MHCUT = self.getNweighted()


        # Send out the ordered dictionary
        return out

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
