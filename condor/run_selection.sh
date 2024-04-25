#!/bin/bash
echo "Run script starting"
source /cvmfs/cms.cern.ch/cmsset_default.sh
xrdcp root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW.tgz ./
export SCRAM_ARCH=slc7_amd64_gcc820
scramv1 project CMSSW CMSSW_12_3_5
tar -xzvf XHYbbWW.tgz
rm XHYbbWW.tgz

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

# Generate the chunking arguments
nchunks=10
# Loop over chunks
for j in $(seq 0 $((nchunks - 1)));
do 
    echo python XHYbbWW_selection.py $* -n $nchunks -j $j
    python XHYbbWW_selection.py $* -n $nchunks -j $j
done

# Get the output file name. The format is:
#       $1    $2     $3   $4   $5     $6       $7   $8  $9   $10     $11   $12
#       -s <SETNAME> -y <YEAR> -v <VARIATION> --HT <HT> -n <NCHUNKS> -j <CHUNK #>
if [ $6 == "None" ]; then 
    filename='XHYbbWWselection_HT'"$8"'_'"$2"'_'"$4"'.root'
else
    filename='XHYbbWWselection_HT'"$8"'_'"$2"'_'"$4"'_'"$6"'.root'

# hadd the output chinks
hadd -fk rootfiles/"$filename" rootfiles/*CHUNK*.root

# move all final selection histos to the EOS
xrdcp -f rootfiles/"$filename" root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/selection/

