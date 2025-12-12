import argparse
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime


class coveragedata:
    def __init__(self, prefix):
        self.prefix = prefix
        self.date = []  # datetime entries
        self.bench = []
        self.games = []
        self.known_nodes = []
        self.unknown_positions = []
        with open(prefix + ".csv") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("Month"):
                    continue
                fields = line.split(",")
                self.date.append(fields[0])
                self.bench.append(int(fields[1]))
                self.games.append(int(fields[2]))
                nodes = int(fields[3])
                positions = int(fields[4])
                unknown_nodes = int(fields[5])
                unknown_positions = int(fields[6])
                self.known_nodes.append((nodes - unknown_nodes) / nodes * 100)
                self.unknown_positions.append(unknown_positions / positions * 100)

    def create_timeseries_graph(self, yrange, y2range, plotStart=0):
        dateData = [datetime.fromisoformat(d + "-01") for d in self.date[plotStart:]]
        benchData = self.bench[plotStart:]
        gamesData = self.games[plotStart:]
        nodesData = self.known_nodes[plotStart:]
        posData = self.unknown_positions[plotStart:]

        fig, ax = plt.subplots()
        nodesColor, posColor = "blue", "firebrick"
        if len(dateData) >= 200:
            nodesDotSize, nodesLineWidth, nodesAlpha = 2, 0.7, 0.75
        elif len(dateData) >= 100:
            nodesDotSize, nodesLineWidth, nodesAlpha = 5, 1, 0.75
        else:
            nodesDotSize, nodesLineWidth, nodesAlpha = 15, 1, 0.75
        ax2 = ax.twinx()

        ax.scatter(
            dateData, nodesData, color=nodesColor, s=nodesDotSize, alpha=nodesAlpha
        )
        mi, ma = min(nodesData), max(nodesData)
        mi, ma = round(mi * 10) / 10, round(ma * 10) / 10
        rangeStr = f"[{mi}%, {ma}%]"
        ax.plot(
            dateData,
            nodesData,
            color=nodesColor,
            linewidth=nodesLineWidth,
            alpha=nodesAlpha,
            label=f"known visits                         (in {rangeStr})",
        )
        ax2.scatter(dateData, posData, color=posColor, s=nodesDotSize, alpha=nodesAlpha)
        mi, ma = min(posData), max(posData)
        mi, ma = round(mi * 10) / 10, round(ma * 10) / 10
        rangeStr = f"[{mi}%, {ma}%]"
        ax2.plot(
            dateData,
            posData,
            color=posColor,
            linewidth=nodesLineWidth,
            alpha=nodesAlpha,
            label=f"unique unknown positions   (in {rangeStr})",
        )
        ax.tick_params(axis="y", labelcolor=nodesColor)
        ax2.tick_params(axis="y", labelcolor=posColor)

        lines_1, labels_1 = ax.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        leg = ax.legend(lines_1 + lines_2, labels_1 + labels_2, fontsize=5)
        colors = [nodesColor, posColor]
        for text, color in zip(leg.get_texts(), colors):
            text.set_color(color)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.setp(
            ax.get_xticklabels(),
            rotation=45,
            ha="right",
            rotation_mode="anchor",
            fontsize=6,
        )
        ax.grid(alpha=0.4, linewidth=0.5)
        prefix = self.prefix.replace("_", r"\_")
        bold = rf"$\bf{{{prefix}}}$"
        fig.suptitle(f"     Progress indicators from {bold}.csv.")
        noStr = f"{min(gamesData)}-{max(gamesData)}"
        ax.set_title(
            f"Based on between {min(gamesData)} and {max(gamesData)} games each month.",
            fontsize=6,
            family="monospace",
        )
        if yrange is not None:
            ax.set_ylim(yrange)
        ymin, ymax = ax.get_ylim()
        print(f"y-range: {ymin} {ymax}")
        if y2range is not None:
            ax2.set_ylim(y2range)
        y2min, y2max = ax2.get_ylim()
        print(f"y2-range: {y2min} {y2max}")

        for i in range(len(benchData)):
            if i == 0 or benchData[i] != benchData[i - 1]:
                ax.axvline(
                    x=dateData[i],
                    color="lightgray",
                    linestyle="--",
                    linewidth=1,
                    alpha=0.7,
                )
                ax.text(
                    x=dateData[i],
                    y=0.999 * ymax,
                    s=f" {benchData[i]}",
                    verticalalignment="top",
                    fontsize=4,
                    color="gray",
                )

        fig.tight_layout(rect=[0, 0, 1, 1.03])
        plt.savefig(self.prefix + bool(plotStart) * str(plotStart) + ".png", dpi=300)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plot data stored in e.g. litrack_unknown2000_d20.csv.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "filename",
        nargs="?",
        help="File with cdb coverage statistics over time.",
        default="litrack.csv",
    )
    parser.add_argument(
        "--yrange",
        nargs=2,
        type=float,
        default=None,
        help="Set a fixed y-range for the time evolution graph.",
    )
    parser.add_argument(
        "--y2range",
        nargs=2,
        type=float,
        default=None,
        help="Set a fixed y2-range for the time evolution graph.",
    )
    args = parser.parse_args()

    prefix, _, _ = args.filename.partition(".")
    data = coveragedata(prefix)
    data.create_timeseries_graph(args.yrange, args.y2range)
