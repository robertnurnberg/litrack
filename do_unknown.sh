#!/bin/bash

# exit on errors
set -e

month=$1
trimmedzst=$2
depths="20 40 60"

for d in $depths; do
  csv=litrack_unknown_d$d.csv
  if [[ ! -f $csv ]]; then
    echo "Month,Bench,Games,Nodes,Positions,Unknown nodes,Unknown positions" >$csv
  fi
  if grep -q "^$month," "$csv"; then
    continue
  fi
  ./fastpopular --file $trimmedzst --maxPlies $d --omitMoveCounter --saveCount --cdb >&fp.log
  rm -f popular.epd
  ./litrack.unknown popular_sorted.epd >&cdbdirect.log
  rm -f popular_sorted.epd
done
