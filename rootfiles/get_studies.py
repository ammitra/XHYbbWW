from TIMBER.Tools.Common import ExecuteCmd

fProcs = open('condor/studies_args.txt','r')
procs = [i.strip().split(' ')[1] for i in fProcs.readlines()]
procs = list(set(procs))

redir = 'root://cmsxrootd.fnal.gov/'
cmd = f'hadd -f -k {redir}/store/user/ammitra/XHYbbWW/studies/Studies_{proc}-Run2.root {redir}/store/user/ammitra/XHYbbWW/studies/Studies_{proc}_*.root'
for proc in procs:
    ExecuteCmd(cmd.format(redir=redir,proc=proc))
