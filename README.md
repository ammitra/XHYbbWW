# X->HY->bbWW
Based off of Lucas Corcodilos' work [here](https://github.com/lcorcodilos/TopHBoostedAllHad).

##1) Populate raw NanoAOD text files
Run ```python raw_nano/get_all_lpc.py``` to get the locations of all the raw NanoAOD data.

##2) Perform snapshot on `raw_nano/` files
To perform a snapshot on a single .txt file holding either data or simulation, run

```
python XHYbbWW_snapshot.py -s [setname] -y [year(16/17/18)] -j [job#] -n [#jobs]
```

where `ijob` is the job number and `njobs` is the number of jobs to split into.

### **Condor**

**Creating an archived environment:**

Use `condor/tar_env.sh` to create a tarball of the current environment and store it in your EOS.

**Arguments file:**

Use `python condor/snapshot_args.py` to generate a list of arguments for the condor job automatically. The list will be written to `condor/snapshot_args.txt`.

The args script will splot the sets into N/2 jobs where N is the total number of raw NanoAOD files. These settings can be changed in the args script.

**Bash script to run on condor node:**

The script `condor/run_snapshot.sh` will run on the condor node and requires that the directory `XHYbbWW` exists in your EOS space. It can be created by running

```
eosmkdir /store/user/ammitra/XHYbbWW
```

(change to your own username)

**Submission:**

First create a symlink to the TIMBER condorHelper script:

```
ln -s $TIMBERPATH/TIMBER/Utilities/Condor/CondorHelper.py
```

Then run 

```
python CondorHelper.py -r condor/run_snapshot.sh -a condor/snapshot_args.txt -i "XHYbbWW_class.py XHYbbWW_snapshot.py"`
```

Here, `-i` incldues local scripts to the node for use. 

**NOTE:** This step assumes that you've created an env tarball as well as a list of jobs to submit in the condor task.

##3) Collect condor snapshot outputs
Jobs automatically get moved to tour EOS space under
