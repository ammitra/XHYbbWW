'''
Script to test whether moving to JRv2 is working properly
'''
from TIMBER.Analyzer import analyzer
import TIMBER.Tools.AutoJME as AutoJME
from TIMBER.Tools.Common import GetJMETag, _year_to_thousands_str
from TIMBER.Analyzer import Calibration

# load analyzer
a = analyzer('signal_1800-800.root')

# load JER correction
jer_tag = GetJMETag("JER",'2017',"MC",True)
jer = Calibration("%s_JER"%'FatJet',"TIMBER/Framework/include/JER_weight.h", [jer_tag,"AK8PFPuppi"], corrtype="Calibration")
