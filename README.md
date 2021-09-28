# X->HY->bbWW
Based off of Lucas Corcodilos' work [here](https://github.com/lcorcodilos/TopHBoostedAllHad).

## 1) Populate raw NanoAOD text files
Run
 
```
python raw_nano/get_all_lpc.py
``` 

to get the locations of all the raw NanoAOD data.

Run 

```
python raw_nano/get_massPts.py
```

to grab all the massPts from Lucas' directories. These files have a specific XMass corresponding to one or more YMasses.

The Signal files have one XMass corresponding to multiple YMasses (sometimes just one YMass). `get_massPts.py` looks up the signal ROOT files on the EOS and searches each of them for the `GenModel_YMass_*` branch under `Events` to determine whether or not the signal sample contains that YMass. All signal files corresponding to the appropriate `<XMASS, YMASS>` pair are then appended to the corresponding `_loc.txt` file. 

## 2) Perform snapshot on `raw_nano/` files
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
python CondorHelper.py -r condor/run_snapshot.sh -a condor/snapshot_args.txt -i "XHYbbWW_class.py XHYbbWW_snapshot.py"
```

Here, `-i` includes local scripts to the node for use.


**NOTE:** This step assumes that you've created an env tarball as well as a list of jobs to submit in the condor task.

## 3) Collect condor snapshot outputs
Job outputs (snapshots) automatically get moved to EOS space under `/store/user/ammitra/XHYbbWW/snapshots/`. The information for those snapshots can be collected with 

```
python trijet_nano/get_all.py
```

## 4) Perform studies 

The script `XHYbbWW_studies.py` takes in the setname, year, and (later) variation of the snapshot ROOT files and creates kinematic plots and N-1 plots from them. To utilize this script, run 

```
python perform_studies.py
```

**UPDATE: (9/27/21)** The `XHYbbWW_studies.py` script now also creates `mX` vs `mY` plots for all QCD, ttbar, and signal files. To achieve this, the WvsQCD score is kept constant along with all kinematic and softdrop mass cuts, and the HbbvsQCD score is varied to encompass the three regions `Hbb < 0.8`, `0.8 < Hbb < 0.98` and `Hbb > 0.98`. The backgrounds are then stitched together in the `XHYbbWW_MXvsMY_plotter.py` scripts and all their combined 2DHistos concatenated. 

## 5) Plots

Run the command with either the `--scale` or `--noscale` arguments to plot the histograms scaled/not scaled to unity, respectively.

```
python XHYbbWW_plotter.py [--scale] [--noscale]
```

**UDPATE: (9/27/21)** To get the 2D histograms of `mX` vs `mY` for the QCD, ttbar, and signal - run:

```
python XHYbbWW_MXvsMY_plotter.py
```

after having run `python perform_studies.py`. This script requires only that the "studies" files have been created and are in the `rootfiles/` directory

**For my own use:** Run 

```
source get_plots.sh filename
```

to create and send `filename.tar.gz` containing the outputted plots from `XHYbbWW_plotter.py` to CMS4. From there you can view them.

One should use the script `GroupImgToPDF` (thanks, Lucas!) to concatenate multiple images into one PDF for quick viewing. To use it, run 

```
python GroupImgToPDF.py -o [output_file] -F [files...]
```

where wildcards for filenames are acceptable
