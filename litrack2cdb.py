import argparse, asyncio, sys, time

sys.path.insert(0, "../cdblib")
import cdblib, chess


class litrack2cdb:
    def __init__(
        self,
        filename,
        output,
        pieceMin,
        concurrency,
        user,
        suppressErrors,
    ):
        self.input = filename
        self.lines = []
        self.scored = 0
        with cdblib.open_file_rt(filename) as f:
            for line in f:
                line = line.strip()
                if line:
                    self.lines.append(line)
                    if not line.startswith("#"):  # ignore comments
                        self.scored += 1
        self.output = open(output, "w")
        self.display = sys.stdout
        self.pieceMin = pieceMin
        print(
            f"Read {self.scored} FENs from file {self.input}.",
            file=self.display,
            flush=True,
        )
        self.concurrency = concurrency
        self.cdb = cdblib.cdbAPI(concurrency, user, not suppressErrors)

    async def parse_all(self, batchSize=None):
        print(
            f"Started parsing the FENs with concurrency {self.concurrency}"
            + (" ..." if batchSize == None else f" and batch size {batchSize} ..."),
            file=self.display,
            flush=True,
        )
        if batchSize is None:
            batchSize = len(self.lines)
        self.tic = time.time()
        for i in range(0, len(self.lines), batchSize):
            tasks = []
            for line in self.lines[i : i + batchSize]:
                tasks.append(asyncio.create_task(self.parse_single_line(line)))

            for parse_line in tasks:
                print(await parse_line, file=self.output)

        elapsed = time.time() - self.tic
        print(f"Done. Parsed {self.scored} FENs in {elapsed:.1f}s.", file=self.display)

    async def parse_single_line(self, line):
        if line.startswith("#"):  # ignore comments
            return line
        if not "moves" in line:  # FEN already in cdb, nothing to do
            return line
        fen, _, moves = line.partition(" moves ")
        moves = moves.split()
        board = chess.Board(fen)
        fen_plus_moves = fen
        still_in_cdb = True
        for m in moves:
            board.push(chess.Move.from_uci(m))
            pc = chess.popcount(board.occupied)  # piece count
            if pc < self.pieceMin or not bool(board.legal_moves):
                break
            if still_in_cdb:
                # r = await self.cdb.readscore(board.epd())
                r = {"status": "unknown"}
                if r.get("status") != "unknown":
                    fen_plus_moves = board.fen()
                else:
                    still_in_cdb = False
                    fen_plus_moves += " moves " + m
            else:
                fen_plus_moves += " " + m
        return fen_plus_moves


async def main():
    parser = argparse.ArgumentParser(
        description="A simple script to find the cdb exit plies for a list of extended FENs stored in a file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input", help="source filename with FENs (w/ or w/o move counters)"
    )
    parser.add_argument(
        "-o",
        "--output",
        help="optional destination filename",
        default="litrack_cdb.epd",
    )
    parser.add_argument(
        "--pieceMin",
        help="Only query positions with at least this many pieces (cdb only stores positions with 8 pieces or more).",
        type=int,
        default=8,
    )
    parser.add_argument(
        "-c",
        "--concurrency",
        help="Maximum concurrency of requests to cdb.",
        type=int,
        default=16,
    )
    parser.add_argument(
        "-b",
        "--batchSize",
        help="Number of FENs processed in parallel. Small values guarantee more responsive output, large values give faster turnaround.",
        type=int,
        default=None,
    )
    parser.add_argument(
        "-u",
        "--user",
        help="Add this username to the http user-agent header.",
    )
    parser.add_argument(
        "-s",
        "--suppressErrors",
        action="store_true",
        help="Suppress error messages from cdblib.",
    )
    args = parser.parse_args()

    l2c = litrack2cdb(
        args.input,
        args.output,
        args.pieceMin,
        args.concurrency,
        args.user,
        args.suppressErrors,
    )

    await l2c.parse_all(args.batchSize)


if __name__ == "__main__":
    asyncio.run(main())
