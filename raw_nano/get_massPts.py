import ROOT
import glob
import subprocess
from TIMBER.Tools.Common import ExecuteCmd
import sys

'''
This script will parse all of the XYH_WWbb_MX_<M>_loc.txt files in the raw_nano/ directory
and look through them to determine the YMass corresponding to the XMass of the file.

Then the YMass will be added as the multiSampleStr parameter to the analyzer ctor in XYHbbWW_clas.py

this should be used instead of raw_nano/get_all_massPts.sh
'''

redirector = 'root://cmsxrootd.fnal.gov/'
base_dir = '/store/user/lcorcodi/XYH_WWbb_gridpacks/'
eosls = 'eos root://cmseos.fnal.gov ls'

# dictionary { XMASS : file locations }
eos = {
    "1300" : 'NMSSM_XYH_WWbb_MX_1300_TuneCP5_13TeV-madgraph-pythia8/NANO_private_July21_expedite/210713_020551/0000/',
    "1500" : 'NMSSM_XYH_WWbb_MX_1500_TuneCP5_13TeV-madgraph-pythia8/NANO_private_July21_expedite/210713_020509/0000/',
    "2000" : 'NMSSM_XYH_WWbb_MX_2000_TuneCP5_13TeV-madgraph-pythia8/NANO_private_July21_expedite/210713_020631/0000/',
    "3000" : 'NMSSM_XYH_WWbb_MX_3000_TuneCP5_13TeV-madgraph-pythia8/NANO_private_July21_expedite/210713_020712/0000/'
}

# we'll grab all of the files in the form { XMASS : [filenames] }
filenames = {}
for k, v in eos.items():
    print("Running eosls {}{}".format(base_dir,v))
    # each key will be identical to that of eos dict, but values will be all files associated w that mass
    filenames[k] = subprocess.check_output(["{} {}{}".format(eosls,base_dir,v)],shell=True).split('\n')
    filenames[k].remove('')    # for some reason, an empty string gets added to the end of each 

# XMass and corresponding YMass(es)
# There is only one YMass for all XMass pts except X=2000
grid = {
    "1300" : ["200"],
    "1500" : ["400"],
    "2000" : ["400", "800"],
    "3000" : ["800"]
}

# now we want to create files of the form XYH_WWbb_MX_<XMASS>_MY_<YMASS>_loc.txt
for xmass, ymasses in grid.items():
    print("Writing XMass={}, YMass={} location files".format(xmass, ymasses))
    # first check to see if we are dealing with xmass==2000 - generalize 
    if (len(ymasses) != 1):
	# create files to store the results
	out_locations = {ymass : open("XYH_WWbb_MX_{}_MY_{}_loc.txt".format(xmass,ymass),'w') for ymass in ymasses}
	# check to see which YMass is associated with this Xmass - loop over all files for this XMass
	for rootfile in filenames[xmass]:
	    print("opening {}".format(rootfile))
	    # this is the proper way to open ROOT file on EOS according to https://uscms.org/uscms_at_work/computing/LPC/usingEOSAtLPC.shtml#workWithROOTFilesInpyScripts
	    f = ROOT.TFile.Open("{}{}{}".format(redirector,base_dir,rootfile))
	    t = f.Get("Events")
	    # now check which ymass is associated with this xmass
	    for ymass in ymasses:
		print("searching {} for YMass={}".format(rootfile,ymass))
		if (t.GetListOfBranches().FindObject("GenModel_YMass_{}".format(ymass)) != None):
		    out_locations[ymass].write("{}{}{}\n".format(redirector,base_dir,rootfile))
		    break
		else:	# we are not looking at the right ymass, pass
		    pass
	# we should now be done - close all files
	for out in out_locations.values():
	    out.close()

    # otherwise we are looking at an XMass file with only one associated YMass
    else:
	out_file = open("XYH_WWbb_MX_{}_MY_{}_loc.txt".format(xmass,ymasses[0]),'w')
	# loop through all files for this XMass
	for name in filenames[xmass]:
	    out_file.write("{}{}{}\n".format(redirector,base_dir,name))
	out_file.close()

