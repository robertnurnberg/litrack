# litrack

Track the coverage of human games from the
[Lichess open database](https://database.lichess.org)
on [chessdb.cn](https://chessdb.cn/queryc_en/) (cdb).
Here we look both at **coverage** of human opening theory, and statistics
of the **exit ply** for the analysed games.

For the opening **coverage** we count the number of known/unknown positions arising
in the monthly rated Lichess games amongst players with an Elo of at least 2200.
For an intermittently updated static dump of cdb we track both the percentage
of unique unknown positions within the first 10, 20 and 30 moves, as well as
the percentage of known "visits", that is, each position that is encountered in
the games is weighted by the number of times it was seen.
Here the starting position is ignored, as well as positions that cannot appear in
cdb, i.e. positions with fewer than eight pieces and positions without a legal
move.

For the **exit ply** statistics, random samples of the monthly rated Lichess games
at various time controls and Elo brackets are analysed. Plots of the exit ply
distribution, for cdb and the dump, can be found below. In addition, the repo
reports on the evolution of the progress indicator
```math
D = N \left(\sum_{i=1}^N \frac{1}{d_i}\right)^{-1},
```
where $d_i$ is the exit ply for the sampled $\approx$ 100K games,
with the convention that $d_i = \infty$ if the game ends in cdb.
Hence $D$ is an approximation of the games' average exit ply on cdb.

---

## Dump coverage

<table>
  <tr>
    <td align="center">
      <img src="images/litrack_coverage2200_d20.png?raw=true" width="100%">
    </td>
    <td align="center">
      <img src="images/litrack_coverage2200_d40.png?raw=true" width="100%">
    </td>
    <td align="center">
      <img src="images/litrack_coverage2200_d60.png?raw=true" width="100%">
    </td>
  </tr>
</table>

<sup>
The progress indicator plots identify the dump used for each data point via
the total number of positions in the dump, see
<a href="https://huggingface.co/datasets/robertnurnberg/chessdbcn">
Hugging Face</a>.
</sup>

---

## cdb exit ply

<table>
  <tr>
    <td align="center">
      <img src="images/litrack_blitz_cdb_log.png?raw=true" width="100%">
    </td>
    <td align="center">
      <img src="images/litrack_rapid_cdb_log.png?raw=true" width="100%">
    </td>
    <td align="center">
      <img src="images/litrack_classical_cdb_log.png?raw=true" width="100%">
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="images/litrack_blitz_cdb.png?raw=true" width="100%">
    </td>
    <td align="center">
      <img src="images/litrack_rapid_cdb.png?raw=true" width="100%">
    </td>
    <td align="center">
      <img src="images/litrack_classical_cdb.png?raw=true" width="100%">
    </td>
  </tr>
  <tr>
    <td align="center"><img src="images/litrack_blitz_cdbtime.png?raw=true" width="100%"></td>
    <td align="center"><img src="images/litrack_rapid_cdbtime.png?raw=true" width="100%"></td>
    <td align="center"><img src="images/litrack_classical_cdbtime.png?raw=true" width="100%"></td>
  </tr>
</table>

---

## Dump exit ply

<table>
  <tr>
    <td align="center">
      <img src="images/litrack_blitz_dump_log.png?raw=true" width="100%">
    </td>
    <td align="center">
      <img src="images/litrack_rapid_dump_log.png?raw=true" width="100%">
    </td>
    <td align="center">
      <img src="images/litrack_classical_dump_log.png?raw=true" width="100%">
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="images/litrack_blitz_dump.png?raw=true" width="100%">
    </td>
    <td align="center">
      <img src="images/litrack_rapid_dump.png?raw=true" width="100%">
    </td>
    <td align="center">
      <img src="images/litrack_classical_dump.png?raw=true" width="100%">
    </td>
  </tr>

  <tr>
    <td align="center"><img src="images/litrack_blitz_dumptime.png?raw=true" width="100%"></td>
    <td align="center"><img src="images/litrack_rapid_dumptime.png?raw=true" width="100%"></td>
    <td align="center"><img src="images/litrack_classical_dumptime.png?raw=true" width="100%"></td>
  </tr>
</table>

<sup>
The progress indicator plots identify the dump used for each data point via
the total number of positions in the dump, see
<a href="https://huggingface.co/datasets/robertnurnberg/chessdbcn">
Hugging Face</a>.
</sup>

---

### Implementation

Via a cron job the script [`do_track.sh`](do_track.sh) regularly does the
following:

* Check the [Lichess open database](https://database.lichess.org) for a new
  monthly release of rated standard chess games.
* Run the awk scripts [`create_tc_Elo_buckets.awk`](create_tc_Elo_buckets.awk)
  and [`filter_clean_Elo.awk`](filter_clean_Elo.awk).
  The former uses reservoir sampling to randomly sample (up to) 100K each for
  the Elo brackets 2200+, 1800-2200, 1400-1800 at blitz, rapid and classical
  time controls. The second script finds all the games between 2200+ Elo players.
  Both scripts only select from human games that terminate normally and have at
  least one (half)move.
* Run a compiled binary of [`litrack2dump.cpp`](litrack2dump.cpp) to
  probe a local cdb dump for the exit plies of the (about) 900K randomly
  sampled games and store the FEN of the final position still in the dump,
  together with the remaining moves of the game, to a file.
* Run the python script [`litrack2cdb.py`](litrack2cdb.py) to
  query cdb for the final known position of these (about) 900K games, starting
  from the output of the previous step.
* Run the python script [`litrack.py`](litrack.py) to extract the exit ply
  statistics from the output produced in the previous two steps.
* Spawn the script [`do_coverage.sh`](do_coverage.sh) to count the number of
  positions in the 2200+ Elo games (blitz, rapid and classical combined) at ply
  depths 20, 40 and 60 that cannot be found in the dump. The script uses
  compiled binaries from [cdbdirect](https://github.com/vondele/cdbdirect) and
  a tailor-made fork of
  [fastpopular](https://github.com/robertnurnberg/fastpopular/tree/litrack.count).
* Run the python scripts [`plotexitply.py`](plotexitply.py) and
  [`plotcoverage.py`](plotcoverage.py) to produce graphical representations of
  the data.

### Credits

* [disservin/chess-library](https://github.com/Disservin/chess-library) : pgn parsing
* [vondele/fastpopular](https://github.com/vondele/fastpopular) : pgn.zst parsing and counting
* [vondele/cdbdirect](https://github.com/vondele/cdbdirect) : probing local cdb dump
* [robertnurnberg/cdblib](https://github.com/robertnurnberg/cdblib) : querying cdb api

## TL;DR

* Choosing a random position from the first 20/40/60 plies of a random Elo
  2200+ game on Lichess (at blitz, rapid or classical TC, and excluding the
  starting position), gives a 97%/61%/44% chance that it is already known to
  cdb.
* An Elo2200+ game on Lichess at classical TC will exit from cdb on average at
  about ply 24.
