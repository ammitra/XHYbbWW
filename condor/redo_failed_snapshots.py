from XHYbbWW_class import SplitUp
import subprocess 

cmd = "eosls -l /store/user/ammitra/XHYbbWW/snapshots | awk '{if ($5 < 10000) print $9}'"
failed = subprocess.check_output(cmd,shell=True,text=True)

failed = failed.split('\n')

out = open('FAILED_SNAPSHOTS.txt','w')
for f in failed:
    out.write(f'{f}\n')
out.close()
