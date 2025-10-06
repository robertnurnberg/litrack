#!/bin/bash

# exit on errors
set -e

lock_file=litrack.lock
first="2013-01"
last="2013-01"
# last=$(date +%Y-%m)  # get today's month
sample_size=100000

if [[ -f $lock_file ]]; then
  echo "Lock file exists, exiting."
  exit 1
fi

touch $lock_file

echo "started at: " $(date)

dbs="dump cdb"
tcs="blitz rapid classical"
lichess_prefix="lichess_db_standard_rated_"

for db in $dbs; do
  for tc in $tcs; do
    csv=litrack_${tc}_$db.csv
    if [[ ! -f $csv ]]; then
      if [ "$db" == "dump" ]; then
        echo "Month,Bench,Elo 2200+,Elo 1800-2199,Elo 1400-1799" >$csv
      else
        echo "Month,Access time,Elo 2200+,Elo 1800-2199,Elo 1400-1799" >$csv
      fi
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
  if [ $(grep -l "$month" litrack_*.csv | wc -l) == 6 ]; then
    continue
  fi
  pgn_prefix=${lichess_prefix}${month}
  pgnzst=${pgn_prefix}.pgn.zst
  if [[ ! -f $pgnzst ]]; then
    echo "Download $pgnzst ..."
    wget -q https://database.lichess.org/standard/${pgnzst}
    echo "Download finished at: " $(date)
  fi

  zstdcat "$pgnzst" | awk -v tcs="$tcs" -v pgn_prefix="$pgn_prefix" -v sample_size="$sample_size" -f create_tc_Elo_buckets.awk

  echo "TC+Elo bucket filtering finished at: " $(date)

  for db in $dbs; do
    for tc in $tcs; do
      csv=litrack_${tc}_$db.csv
      if ! grep -q "$month" "$csv"; then
        echo $month >>$csv
        # python plotdata.py $csv
        #  git add $csv # TODO add png files
      fi
    done
  done
done

#  git diff --staged --quiet || git commit -m "Update results"
#  git push origin master >&push.log

rm -f $lock_file

echo "ended at: " $(date)
