#!/bin/bash

# exit on errors
set -e

lock_file=litrack.lock
first="2025-01"
last="2025-09"
# last=$(date +%Y-%m)  # get today's month
sample_size=100000
elo_buckets="2200 1800_2200 1400_1800"

if [[ -f $lock_file ]]; then
  echo "Lock file exists, exiting."
  exit 1
fi

touch $lock_file

echo "started at: " $(date)

dbs="dump cdb"
tcs="blitz rapid classical"
lichess_prefix="lichess_db_standard_rated_"
out=out.tmp

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

  for tc in $tcs; do
    bench="N/A"
    dump_results=
    cdb_results=
    for elo in $elo_buckets; do
      bucket="${pgn_prefix}_${tc}_Elo$elo"
      pgn="$bucket.pgn"
      dump_output="${bucket}_dump.epd"
      cdb_output="${bucket}_cdb.epd"
      if [[ -f $pgn ]]; then
        ./litrack2dump $pgn $dump_output >&$out
        bench=$(grep Opened $out | awk '{print $4}')
        python litrack2cdb.py $dump_output -o $cdb_output
        dump_results="${dump_results}","$(python litrack.py $dump_output)"
        cdb_results="${cdb_results}","$(python litrack.py $cdb_output)"
      else
        dump_results="${dump_results}",
        cdb_results="${cdb_results}",
      fi
    done
    timestamp=$(date +%Y-%m-%d)
    dump_csv=litrack_${tc}_dump.csv
    cdb_csv=litrack_${tc}_cdb.csv
    echo $month,$bench$dump_results >>$dump_csv
    echo $month,$timestamp$cdb_results >>$cdb_csv
    # python plotdata.py $csv
    #  git add $csv # TODO add png files
  done
done

#  git diff --staged --quiet || git commit -m "Update results"
#  git push origin master >&push.log

rm -f $lock_file

echo "ended at: " $(date)
