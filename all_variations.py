import subprocess

# first perform selection with no variations
subprocess.call('python perform_selection.py',shell=True)

# now perform all variations 
for corr in ['JES','JMS','JER','JMR']:
    for ud in ['up','down']:
	subprocess.call('python perform_selection.py -v {}_{}'.format(corr,ud), shell=True)
