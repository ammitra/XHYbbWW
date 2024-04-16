import glob, os

def GetAllFiles():
    #return [f for f in glob.glob('trijet_nano/*_snapshot.txt') if f != '']
    return [f for f in glob.glob('raw_nano/*.txt') if f != '']
def GetProcYearFromFile(filename):
    pieces = filename.split('/')[-1].split('.')[0].split('_')
    if '.txt' in filename:
        return pieces[0], pieces[1]
    else:
        return pieces[1], pieces[2]

out = open('condor/tagger_efficiency_args.txt','w')

files = GetAllFiles()
for f in files:
    setname, era = GetProcYearFromFile(f)
    if ('NMSSM' not in setname) and ('ttbar' not in setname): continue
    out.write('-s %s -y %s\n'%(setname, era))
