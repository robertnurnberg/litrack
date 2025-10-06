import argparse, os, chess
from multiprocessing import Pool


def abssort_str(d):
    # sort dictionary items by abs(key), with positive entries before negative ones
    l = []
    for key, value in sorted(d.items(), key=lambda t: abs(t[0]) + 0.5 * (t[0] < 0)):
        l.append(f"{key}: {value}")
    return "{" + "; ".join(l) + "}"


def process_line(line):
    line = line.strip()
    if not line or line.startswith("#"):  # skip empty lines and comments
        return None, None

    parts = line.split()
    move = int(parts[5])
    ply = (move - 1) * 2 if parts[1] == "w" else (move - 1) * 2 + 1
    print(" ".join(parts[:6]) + f" ply = {ply}")
    return ply if "moves" in line else -ply


parser = argparse.ArgumentParser(
    description="Extract cdb exit ply statistics from an .epd file.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("filename", help="file with extended FENs")
args = parser.parse_args()

lines = []
with open(args.filename) as f:
    lines = f.readlines()

with Pool(processes=os.cpu_count()) as pool:
    results = pool.map(process_line, lines)

exitplies = {}
for p in results:
    if p is not None:
        exitplies[p] = exitplies.get(p, 0) + 1

print(f"{abssort_str(exitplies)}")
