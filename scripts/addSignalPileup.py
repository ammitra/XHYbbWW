import glob
f = glob.glob('raw_nano/NMSSM*18.txt')
for fname in f:
    proc = fname.split('/')[-1].split('.')[0].split('_')[0]
    xmass = proc.split('-')[2]
    if int(xmass) < 1000:
	xsec = 0.1
    elif (int(xmass) >= 1000) and (int(xmass) < 2000):
	xsec = 0.01
    elif (int(xmass) >= 2000) and (int(xmass) < 3000):
	xsec = 0.001
    else:
	xsec = 0.001
    print('\t"{}":{},'.format(proc,xsec))
