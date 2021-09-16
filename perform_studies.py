import glob
import XHYbbWW_studies
import subprocess

# generate list of all snapshot files in trijet_nano
trijet_files = glob.glob('trijet_nano/*.txt')

# empty dict to hold {setname : era} args
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
    elif 'Data' in name:
	continue 	# we don't run the studies script on data
    else:
	setname = split_name[0]
	era = split_name[1]
	if setname in setname_era:
	    setname_era[setname].append(era)
	else:
	    setname_era[setname] = [era]

# instead of creating a new args file and doing it manually, let's just call the existing script
'''
out = open('study_args.txt','w')
for s, y in setname_era.items():
    # check if this setname has multiple years
    if (len(y) > 1):
	for year in y:
	    out.write('-s {} -y {}\n'.format(s, year))
    else:
        out.write('-s {} -y {}\n'.format(s, y[0]))
out.close()
'''

# make a list of arguments
args = []
for s, ys in setname_era.items():
    # check if this setname has multiple years
    if (len(ys) > 1):
	for year in ys:
	    args.append('-s {} -y {}'.format(s, year))
    else:
	args.append('-s {} -y {}'.format(s, ys[0]))

# now just call run the main loop, which calls the XHYbbWW_studies.py script
if __name__ == "__main__":
# for now, don't worry about multithreading and CLI usage, just run this script. 
    for arg in args:
	subprocess.call("python XHYbbWW_studies.py {}".format(arg), shell=True)
