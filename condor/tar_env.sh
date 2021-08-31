# capture current dir
WD=$(pwd)
cd $CMSSW_BASE/../
tar --exclude-caches-all --exclude-vcs --exclude-caches-all --exclude-vcs -cvzf XHYbbWW.tgz CMSSW_11_1_4 --exclude=tmp --exclude=".scram" --exclude=".SCRAM" --exclude=CMSSW_11_1_4/src/timber-env --exclude=CMSSW_11_1_4/src/XHYbbWW/HWW*.root --exclude=CMSSW_11_1_4/src/XHYbbWW/logs --exclude=CMSSW_11_1_4/src/TIMBER/docs --exclude=CMSSW_11_1_4/src/XHYbbWW/plots
xrdcp -f XHYbbWW.tgz root://cmseos.fnal.gov//store/user/$USER/XHYbbWW.tgz
cd ${WD}
