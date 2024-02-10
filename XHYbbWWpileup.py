import ROOT, glob
from TIMBER.Analyzer import TIMBERPATH, analyzer, Correction
from TIMBER.Tools.AutoPU import MakePU

'''
to be run *before* creating snapshots
'''

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
                        action='store', required=True,
                        help='Setname to process.')
    parser.add_argument('-y', type=str, dest='era',
                        action='store', required=True,
                        help='Year of set (16, 17, 18).')
    args = parser.parse_args()

    fullname = '%s_%s'%(args.setname,args.era)
    print('Analyzing {}'.format(fullname))
    print('Searching for file: \n\t{}'.format('raw_nano/%s.txt'%(fullname)))
    #out = ROOT.TFile.Open('XHYbbWWpileup_{}.root'.format(fullname), 'RECREATE')
    outname = 'XHYbbWWpileup_{}.root'.format(fullname)
    a = analyzer('raw_nano/%s.txt'%(fullname))
    MakePU(a, args.era, ULflag=True, filename=outname, setname=fullname)

    '''
    # get pointer to histogram
    #hptr = MakePU(a, '20%sUL'%args.era, fullname+'.root')
    hptr = MakePU(a, args.era, ULflag=True, filename='') # don't save to root file, just get TH1
    hout = hptr.Clone()
    out.WriteTObject(hout, fullname)
    out.Close()
    '''
