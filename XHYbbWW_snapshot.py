import ROOT, time
ROOT.gROOT.SetBatch(True)
from argparse import ArgumentParser
from TIMBER.Tools.Common import CompileCpp
from XHYbbWW_class import XHYbbWW

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
filename = 'raw_nano/{}_{}.txt'.format(args.setname, args.era)

#CompileCpp('HWWmodules.cc')
selection = XHYbbWW(filename, args.era, args.ijob, args.njobs)
selection.ApplyKinematicsSnap()
out = selection.ApplyStandardCorrections(snapshot=True)

# execute all of the GetValue() calls to access the cutflow information
for cut in ['NPROC','NFLAGS','NJETS','NPT','NETA','NMSD']:
    #getattr(selection,cut).GetValue()
    print('Doing cutflow for: %s'%cut)
    selection.AddCutflowColumn(getattr(selection,cut).GetValue(), cut)

selection.Snapshot(out)

print('%s sec'%(time.time()-start))
