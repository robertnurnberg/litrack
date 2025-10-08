# litrack

Track the coverage of human games from 
[Lichess open database](https://database.lichess.org) 
on [chessdb.cn](https://chessdb.cn/queryc_en/) (cdb). 

In particular, for a monthly random sample of rated Lichess games at various
time controls, the repo finds the **exit ply** on cdb. Plots of its
distribution, both for cdb and for an intermittently updated static dump,
can be found below. In addition, the repo reports on the evolution of the
progress indicator
```math
D = N \left(\sum_i \frac{1}{d_i}\right)^{-1},
```
where $d_i$ is the exit ply for the sampled $\approx$ 100K games,
with the convention that $d_i = \infty$ if the game ends in cdb.
Hence $D$ is an approximation of the games' average exit ply on cdb.

---

# cdb

<table>
  <tr>
    <td align="center">
      <img src="litrack_blitz_cdb.png?raw=true" width="100%">
      <div align="right">
        <a href="litrack_blitz_cdb_log.png?raw=true"><sup><i>log plot</i></sup></a>
      </div>
    </td>
    <td align="center">
      <img src="litrack_rapid_cdb.png?raw=true" width="100%">
      <div align="right">
        <a href="litrack_rapid_cdb_log.png?raw=true"><sup><i>log plot</i></sup></a>
      </div>
    </td>
    <td align="center">
      <img src="litrack_classical_cdb.png?raw=true" width="100%">
      <div align="right">
        <a href="litrack_classical_cdb_log.png?raw=true"><sup><i>log plot</i></sup></a>
      </div>
    </td>
  </tr>

  <tr>
    <td align="center"><img src="litrack_blitz_cdbtime.png?raw=true" width="100%"></td>
    <td align="center"><img src="litrack_rapid_cdbtime.png?raw=true" width="100%"></td>
    <td align="center"><img src="litrack_classical_cdbtime.png?raw=true" width="100%"></td>
  </tr>
</table>
---

## Dump

<p align="center"> <img src="litrack_blitz_dump.png?raw=true"> </p>
<p align="center"> <img src="litrack_rapid_dump.png?raw=true"> </p>
<p align="center"> <img src="litrack_classical_dump.png?raw=true"> </p>

---

<p align="center"> <img src="litrack_blitz_dumptime.png?raw=true"> </p>
<p align="center"> <img src="litrack_rapid_dumptime.png?raw=true"> </p>
<p align="center"> <img src="litrack_classical_dumptime.png?raw=true"> </p>

---

### Implementation

Via a cron job the script [`do_track.sh`](do_track.sh) regularly does the
following:

* Checks [Lichess open database](https://database.lichess.org) for a new monthly
  release of rated standard chess games.
* Runs the awk script [`create_tc_Elo_buckets.awk`](create_tc_Elo_buckets.awk)
  to randomly sample (up to) 100K each for the Elo brackets 2200+, 1800-2200, 
  1400-1800 at blitz, rapid and classical time controls. The script uses 
  reservoir sampling and only selects from games that terminate normally and 
  have at least one (half)move.
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
