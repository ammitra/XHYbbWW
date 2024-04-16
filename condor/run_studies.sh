#!/bin/bash
echo "Run script starting"
source /cvmfs/cms.cern.ch/cmsset_default.sh

# grabs the env tarball and places it in this node environment (is that what it's called?)
xrdcp root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW.tgz ./

# essentially what cmsenv does
export SCRAM_ARCH=slc7_amd64_gcc820
scramv1 project CMSSW CMSSW_12_3_5
tar -xzvf XHYbbWW.tgz
# clear up tarball and remaining junk
rm XHYbbWW.tgz
#rm *.root

mkdir tardir; cp tarball.tgz tardir/; cd tardir/
tar -xzf tarball.tgz; rm tarball.tgz
cp -r * ../CMSSW_12_3_5/src/XHYbbWW/; cd ../CMSSW_12_3_5/src/
echo 'IN RELEASE'
pwd
ls
eval `scramv1 runtime -sh`
rm -rf timber-env
python3 -m venv timber-env
source timber-env/bin/activate
cd TIMBER
source setup.sh
cd ../XHYbbWW

echo python XHYbbWW_studies.py $*
python XHYbbWW_studies.py $*

xrdcp -f rootfiles/*.root root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/studies/
