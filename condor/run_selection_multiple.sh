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

##########################################################################################
# Main loop - we will run all variations in one job instead of in separate jobs.         #
# The arguments sent to this shell script will have the format:                          #
#       $1     $2    $3   $4    $5   $6                                                  #
#       -s <SETNAME> -y <YEAR> --HT <HT>                                                 #
# These arguments will be sent to the run_chunks() function defined below.               #
##########################################################################################
run_chunks() {
    # Arguments are the full args sent to the shell script
    local nchunks=10
    for j in $(seq 0 $(( nchunks - 1 )))
    do
        python XHYbbWW_selection.py $* -n $nchunks -j $j
    done
}

if [[ $2 == *"ttbar"* ]] || [[ $2 == *"NMSSM"* ]]    # PNet systematics + JECs
then
    for v in PNetHbb_up PNetHbb_down PNetWqq_up PNetWqq_down JES_up JES_down JER_up JER_down JES_up JES_down JMS_up JMS_down JMR_up JMR_down None
    do
        run_chunks $* -v $v
        if [[ $v == "None" ]]
        then
            filename='XHYbbWWselection_HT'"$6"'_'"$2"'_'"$4"'.root'
        else
            filename='XHYbbWWselection_HT'"$6"'_'"$2"'_'"$4"'_'"$v"'.root'
        fi
        hadd -fk rootfiles/"$filename" rootfiles/*CHUNK*.root
        xrdcp -f rootfiles/"$filename" root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/selection/
        rm rootfiles/*CHUNK*.root
    done
elif [[ $2 == *"Data"* ]] || [[ $2 == *"QCD"* ]]      # no systematics at all
then
    filename='XHYbbWWselection_HT'"$6"'_'"$2"'_'"$4"'.root'
    run_chunks $* -v None
    hadd -fk rootfiles/"$filename" rootfiles/*CHUNK*.root
    xrdcp -f rootfiles/"$filename" root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/selection/
    rm rootfiles/*CHUNK*.root
else    # VJets, other procs, only JEC systs
    for v in JES_up JES_down JER_up JER_down JES_up JES_down JMS_up JMS_down JMR_up JMR_down None
    do
        run_chunks $* -v $v
        if [[ $v == "None" ]]
        then
            filename='XHYbbWWselection_HT'"$6"'_'"$2"'_'"$4"'.root'
        else
            filename='XHYbbWWselection_HT'"$6"'_'"$2"'_'"$4"'_'"$v"'.root'
        fi
        hadd -fk rootfiles/"$filename" rootfiles/*CHUNK*.root
        xrdcp -f rootfiles/"$filename" root://cmseos.fnal.gov//store/user/ammitra/XHYbbWW/selection/
        rm rootfiles/*CHUNK*.root
    done
fi
