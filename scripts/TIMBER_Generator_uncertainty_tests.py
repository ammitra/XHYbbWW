'''
Script to test out the Parton Shower and QCD Scale uncertainties using TIMBER.
Notably, instead of instantiating corrections for each, this only compiles the script once but then clones the 
original correction object and calls a different constructor each time. 

Proof of concept - in the end, this works and is implemented in XHYbbWW_class.py
'''

from TIMBER.Analyzer import *	# analyzer, Correction
from TIMBER.Tools.Common import CompileCpp

a = analyzer('/uscms/home/ammitra/nobackup/XHYbbWW_analysis/CMSSW_11_1_4/src/XHYbbWW/raw_nano/NMSSM-XHY-1800-800_18.txt')

# FSR/ISR tests
a.Define("ISR__up","PSWeight[2]")
a.Define("ISR__down","PSWeight[0]")
a.Define("FSR__up","PSWeight[3]")
a.Define("FSR__down","PSWeight[1]")
genWCorr    = Correction('genW','TIMBER/Framework/TopPhi_modules/BranchCorrection.cc',corrtype='corr',mainFunc='evalCorrection') # workaround so we can have multiple BCs
a.AddCorrection(genWCorr, evalArgs={'val':'genWeight'})
ISRcorr = genWCorr.Clone("ISRunc",newMainFunc="evalUncert",newType="uncert")
print(ISRcorr.name)
print(ISRcorr._mainFunc)
print(ISRcorr._script)
print(ISRcorr._objectName)
print('Cloning genWCorr to make FSRunc')
FSRcorr = genWCorr.Clone("FSRunc",newMainFunc="evalUncert",newType="uncert")
a.AddCorrection(ISRcorr, evalArgs={'valUp':'ISR__up','valDown':'ISR__down'})
a.AddCorrection(FSRcorr, evalArgs={'valUp':'FSR__up','valDown':'FSR__down'})

# QCD scale tests
# First instatiate a correction module for the factorization correction
facCorr = Correction('QCD_factorization','LHEScaleWeights.cc',corrtype='weight',mainFunc='evalFactorization')
a.AddCorrection(facCorr, evalArgs={'LHEScaleWeights':'LHEScaleWeight'})
# Now do one for the renormalization correction
renormCorr = facCorr.Clone('QCD_renormalization',newMainFunc='evalRenormalization',newType='weight')
a.AddCorrection(renormCorr, evalArgs={'LHEScaleWeights':'LHEScaleWeight'})
# Now do one for the combined correction
combCorr = facCorr.Clone('QCD_combined',newMainFunc='evalCombined',newType='weight')
a.AddCorrection(combCorr, evalArgs={'LHEScaleWeights':'LHEScaleWeight'})

