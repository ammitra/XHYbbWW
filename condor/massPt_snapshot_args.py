import glob

out = open('condor/massPt_snapshot_args.txt','w')
for f in glob.glob('massPts/*.txt'):
    filename = f.split('/')[-1].split('.')[0]
    nfiles = len(open(f,'r').readlines())
    # format XYH_WWbb_MX_<MASS>_loc.txt
    setlist = filename.split('_')
    setname = setlist[2]+'_'+setlist[3]
 
    njobs = int(nfiles/2)
    for i in range(1,njobs+1):
        out.write('-s %s -j %s -n %s \n'%(setname,i,njobs))

out.close()
