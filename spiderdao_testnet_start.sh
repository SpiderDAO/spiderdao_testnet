#!/bin/bash -xv

crd=`pwd`

source spiderdao_env
cd scripts 
./service_start.sh
./spiderdao-local-parachain.sh

cd $crd

cd scripts 
./spiderdao_start.sh

cd $crd
