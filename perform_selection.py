import glob
import XHYbbWW_selection
import subprocess
from argparse import ArgumentParser
from TIMBER.Tools.Common import ExecuteCmd

# generate list of all snapshot files in trijet_nano
trijet_files = glob.glob('trijet_nano/*.txt')

setname_era = {}
for f in trijet_files:
    # get everything after '/' and before '.txt'
    name = f.split('/')[-1].split('.')[0]
    split_name = name.split('_')
    if 'MX' in name:
	setname = "{}_{}_{}_{}".format(split_name[0],split_name[1],split_name[2],split_name[3])
	era = split_name[4]
	if setname in setname_era:
	    # append era to list
            setname_era[setname].append(era)
	else:
	    # create key and list of values
	    setname_era[setname] = [era]
    # DataB1 Events TTree is broken, just skip
    elif 'B1' in name:
	continue
    else:
	setname = split_name[0]
	era = split_name[1]
	if setname in setname_era:
	    setname_era[setname].append(era)
	else:
	    setname_era[setname] = [era]

if __name__ == "__main__":
    # this script will just generate everything. If you want to do individual ones, just use XHYbbWW_selection.py
    args = []
    for setname, years in setname_era.items():
	# first, check if we're doing data, QCD, ttbar, or signal    
	if ('Data' in setname) or ('QCD' in setname):   # NO VARIATIONS - QCD is just for validation so no need for variations
	    # check if there are multiple years
	    if len(years) > 1:
		for year in years:
		    args.append('-s {} -y {}'.format(setname, year))
	    else:
		args.append('-s {} -y {}'.format(setname, years[0]))
	else:   # we are doing ttbar or signal - perform variations and nominal
	    for corr in ['JES','JMS','JER','JMR']:
		for ud in ['up','down']:
	    	    if len(years) > 1:
			for year in years:
			    args.append('-s {} -y {} -v {}_{}'.format(setname, year, corr, ud))
		    else:
			args.append('-s {} -y {} -v {}_{}'.format(setname, years[0], corr, ud))
	    # now add the nominal ones
	    if len(years) > 1:
		for year in years:
		    args.append('-s {} -y {}'.format(setname, year))
	    else:
		args.append('-s {} -y {}'.format(setname, years[0]))

    # now that we have all arguments for XHYbbWW_selection.py, let's run it 
    for arg in args:
	ExecuteCmd('python XHYbbWW_selection {}'.format(arg))

    # after this has created all of the selection files, concatenate the data:
    selection_files = glob.glob('rootfiles/XHYbbWWselection_Data*')
    year_files = {'16':[],'17':[],'18':[]}
    for f in selection_files:
	# separate by year
        if '16' in f:
	    year_files['16'].append(f)
	elif '17' in f:
	    year_files['17'].append(f)
	else:
	    year_files['18'].append(f)

    for year, files in year_files.items():
	haddstr=''
	for f in files:
	    haddstr += '{} '.format(f) 
	#print('hadd -f rootfiles/XHYbbWWselection_Data_{}.root {}'.format(year, haddstr))
	ExecuteCmd('hadd -f rootfiles/XHYbbWWselection_Data_{}.root {}'.format(year, haddstr))
