from TIMBER.Tools.Common import GetJMETag, _year_to_thousands_str

for year in ['16','16APV','17','18']:
    print("-------------------------- {} --------------------------".format(year))
    print("MC:")
    yr = _year_to_thousands_str(year)
    # first do MC
    jes_tag = GetJMETag("JES",year,"MC",ULflag=True)
    jer_tag = GetJMETag("JER",year,"MC",ULflag=True)
    print("\tJES: {}".format(jes_tag))
    print("\tJER: {}".format(jer_tag))
    print("Data:")
    for era in ['A','B','C','D','E','F','G','H']:
	jes_tag = GetJMETag("JES",year,era,ULflag=True)
	if (jes_tag):
	    print("\t{}{}: {}".format(year, era, jes_tag))
	else:
	    print("\t{}{}: no tarball found".format(year,era))
    
