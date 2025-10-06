#!/usr/bin/awk -f

# Processes a PGN stream and performs reservoir sampling to select a fixed
# number of games from each time-control and Elo rating bucket.
#
# Required variables passed via -v:
#   - tcs: Space-separated string of time controls (e.g., "blitz rapid").
#   - pgn_prefix: Base name for output files (e.g., "lichess_db_standard_rated_2023-01").
#   - sample_size: The number of games to sample for each bucket (k).

BEGIN {
  srand();
  split(tcs, target_tcs, " ");
  k = sample_size;
}

# This function determines the bucket and performs reservoir sampling.
function process_game(elo_bracket, bucket_id, n, j, combined_key) {
  if (game_tc == "") {
    return;
  }

  if (w_elo >= 2200 && b_elo >= 2200) {
    elo_bracket = "Elo2200";
  } else if (w_elo >= 1800 && w_elo < 2200 && b_elo >= 1800 && b_elo < 2200) {
    elo_bracket = "Elo1800_2200";
  } else if (w_elo >= 1400 && w_elo < 1800 && b_elo >= 1400 && b_elo < 1800) {
    elo_bracket = "Elo1400_1800";
  } else {
    return;
  }

  bucket_id = game_tc "_" elo_bracket;
  counters[bucket_id]++;
  n = counters[bucket_id];

  # Reservoir Sampling Algorithm:
  if (n <= k) {
    # Keep the first k games
    combined_key = bucket_id SUBSEP n;
    reservoir[combined_key] = game_buffer;
  } else {
    # Create random index 1 <= j <= n, if j <= k replace game stored at index j
    j = 1 + int(rand() * n);
    if (j <= k) {
      combined_key = bucket_id SUBSEP j;
      reservoir[combined_key] = game_buffer;
    }
  }
}

/^\[Event / {
  if (NR > 1) {
    process_game();
  }
  game_buffer = "";
  w_elo = 0;
  b_elo = 0;
  game_tc = "";

  lc_line = tolower($0);
  for (i in target_tcs) {
    tc = target_tcs[i];
    if (index(lc_line, tc)) {
      game_tc = tc;
      break;
    }
  }
}

/\[WhiteElo / { split($0, a, "\""); w_elo=a[2]+0; }
/\[BlackElo / { split($0, a, "\""); b_elo=a[2]+0; }
{ game_buffer = game_buffer $0 "\n"; }

END {
  process_game();

  print "--- Writing sampled games to disk ---" > "/dev/stderr";

  for (bucket_id in counters) {
    outfile = pgn_prefix "_" bucket_id ".pgn";

    final_sample_count = (counters[bucket_id] < k) ? counters[bucket_id] : k;

    print "  -> Writing " final_sample_count " games to " outfile > "/dev/stderr";

    for (i = 1; i <= final_sample_count; i++) {
      combined_key = bucket_id SUBSEP i;
      printf "%s", reservoir[combined_key] > outfile;
    }

    close(cmd);
  }
}
