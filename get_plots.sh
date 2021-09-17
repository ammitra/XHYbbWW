#!/bin/bash

tar -zcvf $1.tar.gz plots/
scp -r $1.tar.gz amitavm@cms4.bu.edu:/home/amitavm/
