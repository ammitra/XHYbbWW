# ParticleNet tagging and mistagging scale factors

This directory contains the scripts used to apply W- and Higgs-tagging (and mistagging) scale factors. 

The scale factors are used to update the Hbb/Wqq-tagging status of the candidate jets on a jet-by-jet basis following the prescription set forth [here](https://twiki.cern.ch/twiki/bin/viewauth/CMS/BTagSFMethods#2a_Jet_by_jet_updating_of_the_b), for both signal and ttbar samples.

# Strategy
1. Data

For data, we simply identify the two W candidates with the `particleNetMD_WvsQCD` discriminant and the W mass window. We then apply consecutively tighter `particleNetMD_HbbvsQCD` discriminant cuts on the third (Higgs) candidate jet, to define the signal region. 

2. Signal MC

The signal is subject to the W- and Higgs-tagging scale factors. We begin by looking at the three candidate jets 

3. TTbar MC
