#!/bin/bash -xv

crd=`pwd`

#Set env variables
source spiderdao_env


cd scripts 
#Starts nginx if setup
./service_start.sh

#Starts polkadot and cumulus runtimes
./spiderdao-local-parachain.sh

cd $crd

cd scripts
#Starts the API and Discord bot
#Should be started after the runtimes are up
./spiderdao_start.sh

cd $crd
