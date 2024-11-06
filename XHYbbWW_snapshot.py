import ROOT, time
ROOT.gROOT.SetBatch(True)
from argparse import ArgumentParser
from TIMBER.Tools.Common import CompileCpp
from XHYbbWW_class import XHYbbWW, SplitUp

parser = ArgumentParser()
parser.add_argument('-s', type=str, dest='setname',
                    action='store', required=True,
                    help='Setname to process.')
parser.add_argument('-y', type=str, dest='era',
                    action='store', required=True,
                    help='Year of set (16, 17, 18).')
parser.add_argument('-j', type=int, dest='ijob',
                    action='store', default=1,
                    help='Job number')
parser.add_argument('-n', type=int, dest='njobs',
                    action='store', default=1,
                    help='Number of jobs')
args = parser.parse_args()


# use the XHYbbWW class to gather all the information automatically
infilename = 'raw_nano/{}_{}.txt'.format(args.setname, args.era)

# Some snapshots fail b/c one file in the TChain has a branch that the other(s) do not. 
# To fix this, we have a list of failed jobs using the current file splits saved under FAILED_SNAPSHOTS.txt
# If a requested snapshot is part of this failed list, then run all of the snapshots individually
f_failed = open('FAILED_SNAPSHOTS.txt','r')
failed = [i.strip() for i in f_failed.readlines()]
# construct the would-be snapshot name 
fname = f'HWWsnapshot_{args.setname}_{args.era}_{args.ijob}of{args.njobs}.root'
if fname in failed:
    print(f'----------------------------------------------------------------------------------')
    print(f'\tWARNING: this job failed due to different columns in the TChain:')
    print(f'\t\t{fname}')
    print(f'\tRunning on each file in the group individually...')
    print(f'----------------------------------------------------------------------------------')
    infiles = SplitUp(infilename,args.njobs)[args.ijob-1]
    for i, infile in enumerate(infiles):
        print(f'Running on individual file {i+1}/{len(infiles)} \n\t{infile}')        
        start = time.time()
        selection = XHYbbWW(infile, args.era, f'{i+1}_of_{args.ijob}', f'{args.njobs}', altfilename=args.setname)
        out = selection.ApplyKinematicsSnap()
        for cut in ['NPROC','NFLAGS','NJETS','NPT','NETA','NMSD']:
            print('Doing cutflow for: %s'%cut)
            selection.AddCutflowColumn(getattr(selection,cut).GetValue(), cut)
        selection.Snapshot(out)
        print('%s sec'%(time.time()-start))

else:
    start = time.time()

    selection = XHYbbWW(infilename, args.era, args.ijob, args.njobs)
    out = selection.ApplyKinematicsSnap()

    # execute all of the GetValue() calls to access the cutflow information
    for cut in ['NPROC','NFLAGS','NJETS','NPT','NETA','NMSD']:
        print('Doing cutflow for: %s'%cut)
        selection.AddCutflowColumn(getattr(selection,cut).GetValue(), cut)

    selection.Snapshot(out)

    print('%s sec'%(time.time()-start))
