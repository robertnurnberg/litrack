#!/bin/bash

dbs="dump cdb"
tcs="blitz rapid classical"
cutoff=60
density=0

for db in $dbs; do
  for tc in $tcs; do
    prefix=litrack_${tc}_$db
    python plotdata.py $prefix.csv --negplot --logplot --density $density --cutOff $cutoff
    mv $prefix.png images/${prefix}_log.png
    python plotdata.py $prefix.csv --negplot --density $density --cutOff $cutoff --AvgMinMaxPlot ${prefix}_avgminmax.png
    mv $prefix.png ${prefix}time.png images/
    git add $prefix.csv images/$prefix.png images/${prefix}_log.png images/${prefix}time.png
  done
done
