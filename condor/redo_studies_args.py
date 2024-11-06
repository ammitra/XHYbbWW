import subprocess

fjobs = open('STUDIES_ARGS.txt','r')
jobs = [i.strip() for i in fjobs.readlines()]
fjobs.close()

fOut = open("REDO_STUDIES_ARGS.txt","w")
for job in jobs:
    proc = job.split(' ')[1]
    year = job.split(' ')[3]
    print(proc,year)
    try:
        f = subprocess.check_output(f'eosls /store/user/ammitra/XHYbbWW/studies | grep CR | grep _{proc}_{year}.root',shell=True,text=True)
    except:
        fOut.write(f'-s {proc} -y {year}\n')
fOut.close()
