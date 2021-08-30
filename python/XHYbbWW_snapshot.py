import ROOT, time
ROOT.gROOT.SetBatch(True)
from argparse import ArgumentParser
from XHYbbWW import XHYbbWW

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

start = time.time()

# use the XHYbbWW class to gather all the information automatically
selection = XHYbbWW('raw_nano/%s_%s.txt'%(args.setname,args.era),int(args.era),args.ijob,args.njobs)
# apply kinematic cuts
out = selection.kinematic_cuts()
# feed outfile to class' Snapshot function
selection.Snapshot(out)
print('%s sec'%(time.time()-start))
