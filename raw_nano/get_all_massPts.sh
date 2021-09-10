#!/bin/bash

# for now, just alter all the files I copied from Jon-Edward's directory to prepend the eos redirector to each of the lines in the X mass location files.

sed -i -e 's#^#root://cmsxrootd.fnal.gov/#' massPts/*.txt
