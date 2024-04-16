#!/bin/bash
echo "Run script starting"
source /cvmfs/cms.cern.ch/cmsset_default.sh
xrdcp root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW.tgz ./
echo "export SCRAM_ARCH=el8_amd64_gcc10"
export SCRAM_ARCH=el8_amd64_gcc10
echo "scramv1 project CMSSW CMSSW_12_3_5"
scramv1 project CMSSW CMSSW_12_3_5
tar -xzvf XHYbbWW.tgz
rm XHYbbWW.tgz

mkdir tardir; cp tarball.tgz tardir/; cd tardir/
tar -xzf tarball.tgz; rm tarball.tgz
cp -r * ../CMSSW_12_3_5/src/XHYbbWW/; cd ../CMSSW_12_3_5/src/
echo 'IN RELEASE'
pwd
ls
echo "scramv1 runtime -sh"
eval `scramv1 runtime -sh`
echo "Creating timber-env virtual environment"
python3 -m venv timber-env
source timber-env/bin/activate
cd TIMBER
source setup.sh
cd ../XHYbbWW

echo python MakeTaggerEfficiencies.py $*
python MakeTaggerEfficiencies.py $*

# move all efficiency rootfiles to the EOS
xrdcp -f ParticleNetSFs/EfficiencyMaps/*.root root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/TaggerEfficiencies/
