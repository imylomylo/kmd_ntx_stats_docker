#!/bin/bash

./mm2 > ./mm2.log &
source userpass
echo $userpass
sleep 5
./version.sh
echo "Starting stats collection.sh"
./start_stats.sh 900
tail -f ./mm2.log
