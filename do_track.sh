#!/bin/bash

# exit on errors
set -e

echo "started at: " $(date)

first="2013-01"
last="2013-01"
# last=$(date +%Y-%m)  # get today's month
SAMPLE_SIZE=100000

dbs="dump cdb"
tcs="blitz rapid classical"
lichess_prefix="lichess_db_standard_rated_"
cdbdirect=../cdbdirect/cdbdirect_threaded.litrack

for db in $dbs; do
  for tc in $tcs; do
    csv=litrack_${tc}_$db.csv
    new=new_${tc}_$db.csv
    if [[ ! -f $csv ]]; then
      echo "Month,Exit ply distribution" >$csv
    fi
    # if necessary, merge results from a previous (interrupted) run
    if [[ -f $new ]]; then
      cat $new >>$csv && rm $new
      # python plotdata.py $csv
    fi
  done
done

# Compute all year-month strings between $first and $last
months=$(
  current_date=$(date -d "$first-01" +%Y-%m-%d)
  end_date=$(date -d "$last-01" +%Y-%m-%d)
  while [[ "$current_date" < "$end_date" || "$current_date" == "$end_date" ]]; do
    date -d "$current_date" +%Y-%m
    current_date=$(date -d "$current_date + 1 month" +%Y-%m-%d)
  done
)

for month in $months; do
  echo $month
  pgn_prefix=${lichess_prefix}${month}
  pgnzst=${pgn_prefix}.pgn.zst
  if [[ ! -f $pgnzst ]]; then
    echo "Download $pgnzst ..."
    wget -q https://database.lichess.org/standard/${pgnzst}
  fi

  zstdcat "$pgnzst" | awk -v tcs="$tcs" -v pgn_prefix="$pgn_prefix" -v sample_size="$SAMPLE_SIZE" -f create_tc_Elo_buckets.awk

  ## echo $month >>$new
done

for db in $dbs; do
  for tc in $tcs; do
    csv=litrack_${tc}_$db.csv
    new=new_${tc}_$db.csv
    if [[ -f $new ]]; then
      cat $new >>$csv && rm $new
      # python plotdata.py $csv
    fi
  #  git add $csv # TODO add png files
  done
done

#  git diff --staged --quiet || git commit -m "Update results"
#  git push origin master >&push.log

echo "ended at: " $(date)
