#!/bin/bash
echo "Run script starting"
echo "Running on: `uname -a`"
echo "System software: `cat /etc/redhat-release`"
echo "Starting singularity container"
#cmssw-el8
echo "In singularity container"

source /cvmfs/cms.cern.ch/cmsset_default.sh
xrdcp root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW.tgz ./
#export SCRAM_ARCH=slc7_amd64_gcc820
export SCRAM_ARCH=el8_amd64_gcc10
scramv1 project CMSSW CMSSW_12_3_5
echo "Unpacking compiled CMSSW environment tarball..."
tar -xzf XHYbbWW.tgz
rm XHYbbWW.tgz

mkdir tardir; cp tarball.tgz tardir/; cd tardir/
tar -xzf tarball.tgz; rm tarball.tgz
cp -r * ../CMSSW_12_3_5/src/XHYbbWW/; cd ../CMSSW_12_3_5/src/
echo 'IN RELEASE'
pwd
ls
#scramv1 b ProjectRename
echo 'scramv1 runtime -sh'
eval `scramv1 runtime -sh`
echo $CMSSW_BASE "is the CMSSW we have on the local worker node"
rm -rf timber-env
echo 'python3 -m venv timber-env'
python3 -m venv timber-env

echo 'source timber-env/bin/activate'
source timber-env/bin/activate
echo "$(which python3)"

cd TIMBER
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/cvmfs/cms.cern.ch/el8_amd64_gcc10/external/boost/1.78.0-0d68c45b1e2660f9d21f29f6d0dbe0a0/lib
echo "STARTING TIMBER SETUP......."
source setup.sh
echo "FINISHED TIMBER SETUP......."
cd ../XHYbbWW

# xrootd debug & certs
#export XRD_LOGLEVEL=Debug
export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates/

# Get the info from the arguments. The format is:
#       $1    $2     $3   $4   $5     $6       $7   $8  $9   $10     $11   $12
#       -s <SETNAME> -y <YEAR> -v <VARIATION> --HT <HT> -n <NCHUNKS> -j <CHUNK #>
# First, get the efficiency map if signal or ttbar
if [[ $2 == *"ttbar"* ]] || [[ $2 == *"NMSSM"* ]]
then
    filename="$2"'_'"$4"'_Efficiencies.root'
    echo 'xrdcp root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/TaggerEfficiencies/'"$filename"' ParticleNetSFs/EfficiencyMaps/'
    xrdcp root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/TaggerEfficiencies/"$filename" ParticleNetSFs/EfficiencyMaps/
fi

# Now run the script
echo python XHYbbWW_selection.py $*
python XHYbbWW_selection.py $*

# move all final selection histos to the EOS
xrdcp -f rootfiles/*.root root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/selection_redo/
