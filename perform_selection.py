import glob
import XHYbbWW_selection
import subprocess
from argparse import ArgumentParser

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
    elif 'Data' in name:
	continue 	# we don't run the studies script on data
    else:
	setname = split_name[0]
	era = split_name[1]
	if setname in setname_era:
	    setname_era[setname].append(era)
	else:
	    setname_era[setname] = [era]

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-v', type=str, dest='variation',
			action='store', default='None',
			help='JES_up, JES_down, JMR_up,...')
    args = parser.parse_args()

    a = []
    for s, ys in setname_era.items():
	if (len(ys) > 1):
	    for year in ys:
		if (args.variation != 'None'):
		    a.append('-s {} -y {} -v {}'.format(s, year, args.variation))
		else:
		    a.append('-s {} -y {}'.format(s, year))
	else:
	    if (args.variation != 'None'):
		a.append('-s {} -y {} -v {}'.format(s, ys[0], args.variation))
	    else:
		a.append('-s {} -y {}'.format(s, ys[0]))

    for arg in a:
	subprocess.call('python XHYbbWW_selection.py {}'.format(arg), shell=True)