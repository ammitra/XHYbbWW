# 2DAlphabet 

After running the `XHYbbWW_selection.py` script, whether on individual setname/year/variation combinations or all together via `perform_selection.py`, the results of the selection are sent to 2DAlphabet for use in the background estimation. This readme will cover the X->HY->bbWW analysis specifically.

Recall that, during the selection process, files of the form `XHYbbWWselection_<setname>_<year>_<variation>.root` are created, each containing 2D template histograms of the form:

```
MXvMY_particleNet_SR_fail__Pileup_up
MXvMY_particleNet_SR_fail__Pileup_down
MXvMY_particleNet_SR_fail__nominal
MXvMY_particleNet_SR_fail__TriggerEff18_down
MXvMY_particleNet_SR_fail__TriggerEff18_up
```

and so on, for all `SR/CR` and `fail/loose/pass` combinations. These file and histogram names are reflected in the config file as seen below. 

## Config file

Terms in the config file in all caps are used for search and replace operations. 

### `PROCESSES`

The `PROCESSES` object defines all the processes that will be included in the background estimation. For `HWW` we are looking at data (`data_obs`), signals (`SIGNAME`), and ttbar. These process objects contain the following parameters:

* `SYSTEMATICS`: This is a list of the systematic uncertainties associated with the given process. The uncertainties listed here must be included in their own object later on in the config file. 

* `SCALE`: How to scale the process in the output histograms 

* `COLOR`: ROOT `kColor` to display the process as in the histogram

* `TYPE`: Whether the process is `DATA`, `SIGNAL`, or `BKG`

* `ALIAS`: Replaces the name of the process sub-object. In this case, the `ALIAS` is set to `Data_18`, since the final data selection files will have been hadd-ed together for their respective years in the form `XHYbbWWselection_Data_<year>.root`. At the time of writing this (11/12/21), only signal samples for 2018 had been generated so we only compare with 2018 data. 

* `TITLE`: How the process will appear in the histograms (uses ROOT LaTeX format)

* `LOC`: The location of the files and histograms associated with the given process. It willbe in the form `path/FILE:HIST`, where `path`, `FILE` and `HIST` are defined in the `GLOBAL` object later on in the config file. 

### `REGIONS`

The `REGIONS` object is where you define the desired regions in which to model the background. The subobjects here must be named in the same way as they appear in the actual histograms in the selection files.

* `PROCESSES`: List of processes for which you want to model the background in this region. List element may themselves be lists (see `SIGNAME`, which is a list of all the signal mass points). 

* `BINNING`: Binning scheme to use for plotting. Binning schemes defined in the `BINNING` object later on in the config file. 

### `GLOBAL`

The `GLOBAL` object defines meta variables used throughout the config file. Variable substitution achieved with the `$` operator 

* `FILE`: The name of the `XHYbbWWselection_$process.root` files, where `$process` is derived from the `PROCESS` sub-object above.

* `FILE_UP` and `FILE_DOWN`: Systematics like `JER`, `JES`, `JMR, and `JMS` and their associated up/down variants are turned into their own selection rootfiles 

* `HIST`: The name of the histogram inside of the selection rootfile (see top of README)

* `HIST_UP` and `HIST_DOWN`: Trigger efficiencies and pileup weighting histograms along with their up/down variants are stored in the selection rootfiles

* `path`: The absolute path to the directory where the selection rootfiles live. Nominally, this is `..../XHYbbWW/rootfiles/`

* `SIGNAME`: This parameter could be named anything, but it is a list of all the signals which we want to include in the background modeling process. The `$process` variable will get replaced by the given list element, where the list element represents the name of a process as given in its selection rootfile name. 

### `BINNING`

The `BINNING` object stores various binning schema. You create an schema name and fill it with the `X` and `Y` sub-objects. **NOTE:** These sub-objects do *not* relate to the X and Y masses. The parameters are used to define the binning on the X and Y axes, respectively. What is displayed on either axis is arbitrary, and is defined using the following parameters: 

* `NAME`: Name of the quantity being plotted on the X/Y axis. In this case, we are plotting the X mass (invariant mass of HWW trijet system) on the X-axis and the Y mass (invariant mass of the two W jets) on the Y-axis. 

* `TITLE`: The axis label, using ROOT LaTeX convention 

* `BINS`: List of bins. These bins can be arbitrarily spaced, but the bin edges **must** correspond to the existing bins in the selection rootfiles. 

    * **NOTE:** One can also use the `MIN`, `MAX`, `NBINS` parameters if you wish to create evenly spaced bins within a range `[MIN, MAX]`. Using a list provides more flexibility, however.

* `SIGSTART` and `SIGEND`: Used for blinding. Denotes where the signal is expected to live


### `SYSTEMATICS`

The `SYSTEMATICS` object stores the actual information regarding all the systematics. These systematics are found both in the selection rootfile names as well as in the histogram names, so care must be taken to specify which is which. 

Each systematic included in the `SYSTEMATICS` list found in each of the `PROCESSES` above must be described in their respective sub-object here. Possible parameters for the systematics include:

* `CODE`: **idk**

* `VAL`: Value for this systematic uncertainty. For example, the systematic uncertainty in the ttbar cross section is 20%. Note, these values seem to be denoted as 1 plus the uncertainty. 

* `ALIAS`: Alias used for find/replace when parsing the config file. This is useful because for a given process we might want to describe the systematic for a given year (i.e. `jmr18`), but the selection rootfiles for any given year are of the form `JMR` without the year, and so on. 

* `UP` and `DOWN`: The path to the systematic with its up/down variant. **NOTE:** It is extremely important that you ensure you have the proper path - for instance:

    * `JMS`, `JMR`, `JES`, and `JER` jet energy corrections and their associated up/down variants are all given their own individual selection rootfile. Therefore, we specify `path/FILE_UP/DOWN:HIST`

    * `Pileup` and `TriggerEff<year>` corrections and their up/down variants are instead given their own histograms. Therefore, we specify `path/FILE:HIST_UP/DOWN`

* `SIGMA`: Standard deviation 

### `OPTIONS`

The `OPTIONS` object defines more meta options for use throughout the entire background modeling process. 

**WIP**
