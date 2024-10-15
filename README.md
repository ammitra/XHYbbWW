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

## 2) Create pileup distributions for pileup weights
This step is handled by `XHYbbWWpileup.py`. To run on individual files:

```
python XHYbbWWpileup.py -s <setname> -y <year>
```

Or, more appropriately, run with condor via

```
python CondorHelper.py -r condor/run_pileup.sh -a condor/pileup_args.txt -i "XHYbbWWpileup.py raw_nano/"
```

after having run `python condor/pileup_args.py` to generate the arguments txt file.

Then, collect the outputs to one local file called `XHybbWWpileup.root` using 

```
scripts/get_pileup_file.sh
```

## 3) Perform snapshot on `raw_nano/` files
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

## 4) Collect condor snapshot outputs
Job outputs (snapshots) automatically get moved to EOS space under `/store/user/ammitra/XHYbbWW/snapshots/`. The information for those snapshots can be collected with 

```
python trijet_nano/get_all.py
```

## 5) Making trigger efficiencies
The trigger efficiency is measured in the SingleMuon dataset separately for the three years, using the `HLT_Mu50` trigger as a reference. It was discovered that, during run 2017B certain substructure- and grooming-based triggers were not available. Therefore, including run 2017B into the total 2017 dataset caused the efficiency of the entire year to drop dramatically. Therefore, the efficiency is measured separately for 2017B, but this run is dropped from the total 2017 dataset when measuring the efficiency for the whole year. Run 2017B accounts for ~12% of the total 2017 JetHT dataset and ~8% of the total SingleMuon dataset, after preselection/snapshotting (see `scripts/check2017fraction.py`). Therefore, we apply the 2017B efficiency to 12% of the 2017MC to account for this difference in efficiency (see the main function in `XHYbbWW_selection.py`).

Run `XHYbbWWtrigger.py` to generate the 1D efficiencies as a function of trijet mass or HT. Based on studies and intuition from B2G-21-002 (see slides 5 and 6 [here](https://indico.cern.ch/event/1046716/contributions/4432638/attachments/2276873/3868137/WWW_0lep_approval_v3.pdf)), it is determined that we must demand HT > 1200 GeV and mj0,mj1,mj2 > 50,40,40 in order to achieve (mostly) >99% efficiency across all three years. 

Run `XHYbbWWtrigger2d.py` to generate the histograms of 2D trigger efficiency as a function of average jet mass and trijet mass. We use average jet mass as proxy for the Higgs mass, since we have performed no tagging at the point when these efficiencies are created. **NOTE:** The `XHYbbWWtrigger2d.py` script will output the ROOT files containing the efficiency histos to the `triggers/` directory. You must copy the ROOT files corresponding to the desired cut on HT to the main analysis directory so that they are included when you run `condor/tar_env.sh` for selection studies. The selection script (`XHYbbWW_selection.py`) relies on the 2D trigger efficiency histos which have the form `HWWtrigger2D_{year}.root`, where `year` can be `16`, `17`, `17B`, or `18`.

The triggers used in this analysis are as follows:
| Dataset  | Triggers |
| -------- | -------- |
| 2016  | `HLT_PFHT800`, `HLT_PFHT900`  |
| 2017B | `HLT_PFHT1050`, `HLT_AK8PFJet500` |
| 2017  | `HLT_PFHT1050`, `HLT_AK8PFJet500`, `HLT_AK8PFHT750_TrimMass50`, `HLT_AK8PFHT800_TrimMass50`, `HLT_AK8PFJet400_TrimMass30` |
| 2018  | `HLT_PFHT1050`, `HLT_AK8PFJet400_TrimMass30`, `HLT_AK8PFHT850_TrimMass50` |

<details>
<summary>Old trigger efficiency info (pre Oct. 25, 2022)</summary>
<br>
First, run `source scripts/get_snapshots.sh` to gather all of the snapshots on the EOS locally, in a directory one above this (`../trijet_nano_files/snapshots`). 

Then, run `python XHYbbWWtrigger.py` to to hadd all of the data snapshots and backfill any empty trigger entries from sub-year eras before making the trigger efficiencies.

**NOTE:** `DataB1` for year 2016 has empty `Events` TTree - it is not included in the hadded 2016 data file.
</details>

## 6) Perform studies 

The script `XHYbbWW_studies.py` takes in the setname, year, and (later) variation of the snapshot ROOT files and creates kinematic plots and N-1 plots from them. To utilize this script, run 
```
python perform_studies.py
```

If you want to generate MXvsMY plots in the SR (`WvsQCD > 0.8`), you must define `W = [0.8]` on line 161 of `XHYbbWW_studies.py`. If you want to generate these plots in the CR, you must instead define `W = [0.3, 0.8]`, where the list elements denote the W score range.

**UPDATE: (9/27/21)** The `XHYbbWW_studies.py` script now also creates `mX` vs `mY` plots for all QCD, ttbar, and signal files. To achieve this, the WvsQCD score is kept constant along with all kinematic and softdrop mass cuts, and the HbbvsQCD score is varied to encompass the three regions `Hbb < 0.8`, `0.8 < Hbb < 0.98` and `Hbb > 0.98`. The backgrounds are then stitched together in the `XHYbbWW_MXvsMY_plotter.py` scripts and all their combined 2DHistos concatenated. 

**UPDATE: (10/7/22)** You can now offload studies to condor. First create a condor directory `/store/user/ammitra/XHYbbWW/studies/`, then run 

```
python CondorHelper.py -r condor/run_studies.sh -a condor/studies_args.txt -i "XHYbbWW_class.py XHYbbWW_studies.py"
```
Then, get the studies plots with `python rootfiles/get_studies.py`

## 7) Plots

Run the command with either the `--scale` or `--noscale` arguments to plot the histograms scaled/not scaled to unity, respectively.

```
python XHYbbWW_plotter.py [--scale] [--noscale]
```

Ideally, `--noscale` is used. 

2D histograms of `mX` vs `mY` for the QCD, ttbar, and signal are generated by `XHYbbWW_MXvsMY_plotter.py`. This script is automatically called by the plotter script, and it generates the 2D distributions of the invariant masses of X and Y as well as the projection onto the Y mass axis for both CR and SR in the fail, loose, and tight regions. 


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

## 8) Tagger efficiencies

ParticleNet tagging and mistagging SF application relies on the efficiencies of generator-matched jets tagged by the given tagger. These efficiency maps are binned in $p_T$ and $\eta$ and are generated by `MakeTaggerEfficiencies.py`. These maps must be generated for every process, and so a script has been created to generate the arguments for Condor as well as submit the jobs. To generate the arguments:

```
python condor/make_tagger_efficiency_args.py
```

To submit the jobs to Condor:

```
python CondorHelper.py -r condor/run_tagger_efficiencies.sh -a condor/tagger_efficiency_args.txt -i "XHYbbWW_class.py MakeTaggerEfficiencies.py"
```

## 8) Selection & 2DAlphabet

The signal region is given by keeping the WvsQCD score greater than 0.8, the control region keeps the WvsQCD score in between 0.3 and 0.8. These regions are defined in the `XHYbbWW_selection.py` script, and both regions are looped over while varying the Hbb score, creating fail, loose, and tight regions for both the SR and CR. 

* **fail:**    `Hbb < 0.8`
* **loose:**   `0.8 < Hbb < 0.98`
* **tight:**   `Hbb > 0.98`

The script generates the template histograms of the X and Y masses in the SR and CR, for a given variation. 

To generate the histograms for 2DAlphabet on a given setname and year, run:

```
python XHYbbWW_selection.py -s [setname] -y [year] [-v variation]
```

Where the variation flag `-v` may be omitted if there is no desired variation to be made. This script:

* Performs selection on all data (except DataB1, whose `Events` TTree is broken so it's skipped) and QCD with NO variations. QCD is just used for validation, so there's no need to run any JMS, JMR, JES, JER variations.  
* Performs selection on all signal and ttbar with all variations (including no variations)

Since there are many setnames, years, and variations, this is best done in parallel using Condor. To aid in this, the script `condor/selection_args.py` generates a .txt file with all possible setname, year, and variation combinations. Then run 

```
python CondorHelper.py -r condor/run_selection.sh -a condor/selection_args.txt -i "XHYbbWW_class.py XHYbbWW_selection.py"
```

The finished files will reside on the EOS, so use `scripts/get_selection.sh` to recover the selection directory, then just move those files to the `rootfiles/` directory

There is an additional directory `twoD_fits` which holds the JSON config file and python script for use with 2DAlphabat to perform the background estimation. These files are not for use with this repository, but the background estimation depends on the selection files generated in step 8.  

## **NOTES**

* **July 11, 2024** For some reason some of the ttbar and W+jets samples don't work when making an analyzer using all files. Something to do with the TTreeReader and TChain. Who knows. A workaround is to run selection for every snapshot file for these problematic sets individually then `hadd` the results together. To do so:

1. Run `python condor/redo_failed_selection_args.py` to generate the args for the jobs that failed automatically
2. Make a directory `/store/user/$USER/XHYbbWW/selection_redo` on EOS to store the individual files
3. Run `python CondorHelper.py -r condor/run_selection_redo.sh -a condor/redo_failed_selection_args.txt -i "XHYbbWW_class.py XHYbbWW_selection.py"`
4. Hadd the individual files into their proper location using `python rootfiles/get_all_failed.py`
5. You can check that all files in the selection dir on EOS are good by doing `eosls -l /store/user/ammitra/XHYbbWW/selection | awk '{if ($5 < 1000) print $9}'` and checking that there is no output.
6. All files can be hadded appropriately using `python rootfiles/get_all.py`


* **DEPRECATED AS OF 5/16/24** When running over raw signal files (located in `raw_nano/XYH_WWBB_MX_XMASS_MY_YMASS_loc.txt`) with an analyzer module, then you have to specify the parameter `multiSampleStr` in the analyzer constructor, where the `multiSampleStr` is the desired Y mass associated with the X mass of the file. This is because there are multiple Y masses associated with the X mass, so this ensures that the proper `genEventWeight_Sum` branch is captured by the analyzer.

* The script `scripts/get_snapshots.sh` populates the directory `trijet_nano_files/` one directory above this on the LPC with the snapshots directory on the EOS. This is then used in the trigger efficiency script 

* **BAD FILES:** The following raw NanoAOD files have some sort of corruption and should not be used, and are therefore removed from the `raw_nano/` files:
    * `ttbar-allhad`, 2017:
        * `/store/mc/RunIISummer20UL17NanoAODv9/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/NANOAODSIM/106X_mc2017_realistic_v9-v1/80000/5ED11CB0-681A-F543-8204-9E4F326F7F29.root` - `Error in <TBranch::GetBasket>: File: root://cmsxrootd.fnal.gov//store/mc/RunIISummer20UL17NanoAODv9/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/NANOAODSIM/106X_mc2017_realistic_v9-v1/80000/5ED11CB0-681A-F543-8204-9E4F326F7F29.root at byte:0, branch:genWeight, entry:84832, badread=0, nerrors=1, basketnumber=23` - this corresponded to the snapshot `4of99` for this year
