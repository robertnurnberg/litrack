#!/usr/bin/awk -f

# Filters human games where both players have Elo >= elo, output to stdout.
#
# Required variables passed via -v:
#   - tcs: Space-separated string of time controls (e.g., "blitz rapid").
#   - elo: minimum Elo value

BEGIN {
  split(tcs, target_tcs, " ");
}

function process_game() {
  if (game_tc != "" && w_elo >= elo && b_elo >= elo &&
      w_title != "BOT" && b_title != "BOT" && termination == "Normal" &&
      has_moves) {
    printf "%s", game_buffer;
  }
}

/^\[Event / {
  if (NR > 1) {
    process_game();
  }
  game_buffer = "";
  w_elo = 0;
  b_elo = 0;
  w_title = "";
  b_title = "";
  game_tc = "";
  termination = "";
  has_moves = 0;

  lc_line = tolower($0);
  for (i in target_tcs) {
    tc = target_tcs[i];
    if (index(lc_line, tc " ")) {
      game_tc = tc;
      break;
    }
  }
}

/\[WhiteElo / { split($0, a, "\""); w_elo=a[2]+0; }
/\[BlackElo / { split($0, a, "\""); b_elo=a[2]+0; }
/\[WhiteTitle / { split($0, a, "\""); w_title=a[2]; }
/\[BlackTitle / { split($0, a, "\""); b_title=a[2]; }
/\[Termination / { split($0, a, "\""); termination=a[2]; }
/^1\./ { has_moves = 1; }

{ game_buffer = game_buffer $0 "\n"; }

END {
  process_game();
}
