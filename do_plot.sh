#!/bin/bash

dbs="dump cdb"
tcs="blitz rapid classical"
cutoff=60
density=1
out=plot.log

for db in $dbs; do
  # first obtain the common y-axis range
  ymin=
  ymax=
  tymin=
  tymax=
  for tc in $tcs; do
    prefix=litrack_${tc}_$db
    python plotdata.py $prefix.csv --negplot --density $density --cutOff $cutoff >&$out
    mi=$(grep Distro $out | awk '{print $4}')
    ma=$(grep Distro $out | awk '{print $5}')
    ymin="$ymin $mi"
    ymax="$ymax $ma"
    mi=$(grep Time $out | awk '{print $3}')
    ma=$(grep Time $out | awk '{print $4}')
    tymin="$tymin $mi"
    tymax="$tymax $ma"
  done
  ymin=$(echo $ymin | tr ' ' '\n' | sort -n | head -n 1)
  ymax=$(echo $ymax | tr ' ' '\n' | sort -n | tail -n 1)
  tymin=$(echo $tymin | tr ' ' '\n' | sort -n | head -n 1)
  tymax=$(echo $tymax | tr ' ' '\n' | sort -n | tail -n 1)

  # now use the same y-axis range for all the plots
  for tc in $tcs; do
    prefix=litrack_${tc}_$db
    python plotdata.py $prefix.csv --negplot --logplot --density $density --cutOff $cutoff --distroYrange $ymin $ymax --timeYrange $tymin $tymax >&$out
    mv $prefix.png images/${prefix}_log.png
    python plotdata.py $prefix.csv --negplot --density $density --cutOff $cutoff --AvgMinMaxPlot ${prefix}_avgminmax.png --distroYrange $ymin $ymax --timeYrange $tymin $tymax >&$out
    mv $prefix.png ${prefix}time.png images/
    git add $prefix.csv images/$prefix.png images/${prefix}_log.png images/${prefix}time.png
  done
done
