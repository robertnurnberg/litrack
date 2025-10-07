# litrack

Track the coverage of human games from 
[Lichess open database](https://database.lichess.org) 
on [chessdb.cn](https://chessdb.cn/queryc_en/) (cdb).

### Implementation

Via a cron job the script [`do_track.sh`](do_track.sh) regularly does the
following:

* Checks [Lichess open database](https://database.lichess.org) for a new monthly
  release of rated standard chess games.
* Runs the awk script [`create_tc_Elo_buckets.awk`](create_tc_Elo_buckets.awk)
  to randomly sample 100K each for the Elo brackets 2200+, 1800-2200, 1400-1800
  at blitz, rapid and classical time controls. The script uses reservoir
  sampling and only selects from games that terminate normally and have at
  least one (half)move.
* Runs a compiled binary of [`litrack2dump.cpp`](litrack2dump.cpp) to 
  probe a local cdb dump for the exit plies of the 900K games and stores the
  FEN of the final position still in the dump, together with the remaining
  moves of the game, to a file.
* Runs the python script [`litrack2cdb.py`](litrack2cdb.py) to
  query cdb for the final known position of the 900K games, starting from
  the output of the previous step.
* Runs the python scripts [`litrack.py`](litrack.py) and
  [`plotdata.py`](plotdata.py) to produce graphical representations of the
  data.

### Credits

* [disservin/chess-library](https://github.com/Disservin/chess-library) : pgn parsing
* [vondele/cdbdirect](https://github.com/vondele/cdbdirect) : probing local cdb dump
* [robertnurnberg/cdblib](https://github.com/robertnurnberg/cdblib) : querying cdb api
