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

    # setname: 
    #	DataX		MX_XMASS_MY_YMASS
    fullname = '%s_%s'%(args.setname,args.era)
    out = ROOT.TFile.Open('XHYbbWWpileup_{}.root'.format(fullname), 'RECREATE')

    # if signal files, format is raw_nano/XYH_WWbb_MX_XMASS_MY_YMASS_loc.txt
    if 'MX' in fullname:
	# need to consider the multiSampleStr - this is the YMASS in MX_XMASS_MY_YMASS
	ymass = args.setname.split('_')[-1]
	a = analyzer('raw_nano/XYH_WWbb_{}_loc.txt'.format(args.setname),multiSampleStr=ymass)
    else:
        a = analyzer('raw_nano/%s.txt'%(fullname))
    h = MakePU(a, '20%sUL'%args.era, fullname+'.root')
    out.cd()
    h.Write()
    out.Close()
