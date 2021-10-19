#!/bin/bash
echo "Run script starting"
source /cvfms/cms.cern.ch/cmsset_default.sh
xrdcp root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW.tgz ./
export SCRAM_ARCH=slc7_amd64_gcc820
scramv1 project CMSSW CMSSW_11_1_4
tar -xzvf XHYbbWW.tgz
rm XHYbbWW.tgz

mkdir tardir; cp tarball.tgz tardir/; cd tardir/
tar -xzf tarball.tgz; rm tarball.tgz
cp -r * ../CMSSW_11_1_4/src/XHYbbWW/; cd ../CMSSW_11_1_4/src/
echo 'IN RELEASE'
pwd
ls
eval`scramv1 runtime -sh`
rm -rf timber-env
python -m virtualenv timber-env
source timber-env/bin/activate
cd TIMBER
source setup.sh
cd ../XHYbbWW

echo python XHYbbWWpileup.py $*
python XHYbbWWpileup.py $*


xrdcp -f XHYbbWWpileup_*.root root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/pileup/
