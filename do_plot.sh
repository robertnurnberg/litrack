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
    python plotexitply.py $prefix.csv --negplot --density $density --cutOff $cutoff >&$out
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
    python plotexitply.py $prefix.csv --negplot --logplot --density $density --cutOff $cutoff --distroYrange $ymin $ymax --timeYrange $tymin $tymax >&$out
    mv $prefix.png images/${prefix}_log.png
    python plotexitply.py $prefix.csv --negplot --density $density --cutOff $cutoff --AvgMinMaxPlot ${prefix}_avgminmax.png --distroYrange $ymin $ymax --timeYrange $tymin $tymax >&$out
    mv $prefix.png ${prefix}time.png images/
    git add $prefix.csv images/$prefix.png images/${prefix}_log.png images/${prefix}time.png
  done
done

depths="20 40 60"
coverageElo=2200
ymin=40
ymax=100
y2min=0
y2max=85
for d in $depths; do
  prefix=litrack_coverage${coverageElo}_d$d
  python plotcoverage.py ${prefix}.csv --yrange $ymin $ymax --y2range $y2min $y2max >&$out
  mv $prefix.png images/
  git add $prefix.csv images/$prefix.png
done
