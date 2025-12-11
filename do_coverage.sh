#!/bin/bash

# exit on errors
set -e

month=$1
coverageElo=$2
lichess_prefix="lichess_db_standard_rated_"
pgn_prefix=${lichess_prefix}${month}
trimmedzst=${pgn_prefix}_Elo${coverageElo}.pgn.zst
depths="20 40 60"
score_locally="../cdblib/addons/score_fens_locally.py"
bench="N/A"

for d in $depths; do
  csv=litrack_coverage${coverageElo}_d$d.csv
  if [[ ! -f $csv ]]; then
    echo "Month,Bench,Games,Nodes,Positions,Unknown nodes,Unknown positions" >$csv
  fi
  if grep -q "^$month," "$csv"; then
    continue
  fi
  ./fastpopular.count --file $trimmedzst --maxPlies $d --omitMoveCounter --saveCount --cdb >&fp.log
  rm -f popular.epd
  games=$(grep Retained fp.log | awk '{print $12}')
  nodes=$(grep Retained fp.log | awk '{print $9}')
  pos=$(grep Retained fp.log | awk '{print $2}')
  if [[ -f known.epd.gz ]]; then
    tmpname="$(mktemp -q)"
    python "$score_locally" popular_count.epd known.epd.gz 1>"$tmpname" 2>scl.log
    mv "$tmpname" known.epd
    grep -v cdb known.epd >cdb_input.epd || true
    rm -f known.epd.gz
    pigz known.epd
    rm -f popular_count.epd
  else
    cp popular_count.epd cdb_input.epd
    mv popular_count.epd known.epd
    pigz known.epd
  fi
  unknown_pos=0
  unknown_nodes=0
  count_input=$(wc -l <cdb_input.epd)
  if [ $count_input -ne 0 ]; then
    ./cdbdirect_threaded cdb_input.epd >&cdbdirect.log
    bench=$(grep Opened cdbdirect.log | awk '{print $4}')
    unknown_pos=$(grep "unknown fens:" cdbdirect.log | awk '{print $3}')
    grep -v cdb cdbdirect.epd >unknown.epd || true
    count_unknown=$(wc -l <unknown.epd)
    if [ $count_unknown -ne 0 ]; then
      unknown_nodes=$(awk '{ sum += $7 } END { print sum }' unknown.epd)
    fi
    if [[ "$d" != "60" ]]; then
      tmpname="$(mktemp -q)"
      python "$score_locally" known.epd.gz cdbdirect.epd 1>"$tmpname" 2>scl.log
      mv "$tmpname" known.epd
      rm -f known.epd.gz
      pigz known.epd
    fi
    rm -f cdbdirect.epd
  fi
  echo $month,$bench,$games,$nodes,$pos,$unknown_nodes,$unknown_pos >>$csv
done
rm -f known.epd.gz
grep -v 'c0 1$' unknown.epd > coverage_upload.epd
rm -f unknown.epd
