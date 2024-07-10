import ROOT, glob
from TIMBER.Analyzer import TIMBERPATH, analyzer, Correction
from TIMBER.Tools.AutoPU import MakePU

'''
to be run *before* creating snapshots
'''

def SplitUp(filename,npieces,nFiles=False):
    '''Take in a txt file name where the contents are root
    file names separated by new lines. Split up the files
    into N lists where N is `npieces` in the case that `nFiles == False`.
    In the case that `nFiles == True`, `npieces` is treated as the
    number of files to have per list.
    '''
    files = open(filename,'r').readlines()
    nfiles = len(files)

    if npieces > nfiles:
        npieces = nfiles

    if not nFiles: files_per_piece = float(nfiles)/float(npieces)
    else: files_per_piece = npieces

    out = []
    iend = 0
    for ipiece in range(1,npieces+1):
        piece = []
        for ifile in range(iend,min(nfiles,int(ipiece*files_per_piece))):
            piece.append(files[ifile].strip())

        iend = int(ipiece*files_per_piece)
        out.append(piece)
    return out

if __name__ == "__main__":
    from argparse import ArgumentParser

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

    inputFile = 'raw_nano/%s_%s.txt'%(args.setname, args.era)
    print('Loading input file %s'%inputFile)
    infiles = SplitUp(inputFile, args.njobs)[args.ijob-1]
    print('Loading sub-files:')
    print(',\n'.join(infiles))
    a = analyzer(infiles)
    outname = 'XHYbbWWpileup_{}_{}_{}of{}.root'.format(args.setname, args.era, args.ijob, args.njobs)
    fullname = '%s_%s'%(args.setname, args.era)
    MakePU(a, args.era, ULflag=True, filename=outname, setname=fullname)

    '''
    fullname = '%s_%s'%(args.setname,args.era)
    print('Analyzing {}'.format(fullname))
    print('Searching for file: \n\t{}'.format('raw_nano/%s.txt'%(fullname)))
    #out = ROOT.TFile.Open('XHYbbWWpileup_{}.root'.format(fullname), 'RECREATE')
    outname = 'XHYbbWWpileup_{}.root'.format(fullname)
    a = analyzer('raw_nano/%s.txt'%(fullname))
    MakePU(a, args.era, ULflag=True, filename=outname, setname=fullname)
    '''

    '''
    # get pointer to histogram
    #hptr = MakePU(a, '20%sUL'%args.era, fullname+'.root')
    hptr = MakePU(a, args.era, ULflag=True, filename='') # don't save to root file, just get TH1
    hout = hptr.Clone()
    out.WriteTObject(hout, fullname)
    out.Close()
    '''
