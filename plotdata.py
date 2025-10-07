import argparse, ast
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from matplotlib.offsetbox import AnchoredOffsetbox, TextArea, HPacker, VPacker
from matplotlib.ticker import MaxNLocator
from matplotlib.ticker import FuncFormatter

depthIndicatorStr = ""


def depth_indicator(d):
    global depthIndicatorStr
    depthIndicatorStr = r"$N \left(\sum_i\ \frac{1}{d_i}\right)^{-1}$"
    s = NoP = 0
    for k, v in d.items():
        NoP += v
        if k > 0:
            s += v / k
    return NoP / s, NoP


def depth_average(d):
    c = s = 0
    for k, v in d.items():
        if k > 0:
            s += v * k
            c += v
    return s / c


def shrink_number_string(s):
    s = str(s)
    if s.endswith("0" * 9):
        return s[:-9] + "G"
    elif s.endswith("0" * 6):
        return s[:-6] + "M"
    elif s.endswith("0" * 3):
        return s[:-3] + "K"


class litrackdata:
    def __init__(self, prefix):
        self.prefix = prefix
        self.date = []  # datetime entries
        self.elo_buckets = 3
        self.depths = [[] for _ in range(self.elo_buckets)]  # depth distributions
        self.eloStr = [""] * self.elo_buckets
        with open(prefix + ".csv") as f:
            for line in f:
                line = line.strip()
                if line.startswith("Month"):
                    fields = line.split(",")
                    for elo in range(self.elo_buckets):
                        self.eloStr[elo] = fields[2 + elo]
                elif line:
                    fields = line.split(",")
                    month = fields[0]
                    self.date.append(month)
                    for elo in range(self.elo_buckets):
                        dictStr = fields[2 + elo].replace(";", ",")
                        self.depths[elo].append(ast.literal_eval(dictStr))

    def create_distribution_graph(self, logplot, negplot, densityplot):
        color, edgecolor, label = ["red", "blue"], ["yellow", "black"], [None, None]
        fig, ax = plt.subplots(self.elo_buckets, 1, sharex=True)
        perBin = 1
        dictList = [[None, None] for _ in range(self.elo_buckets)]
        # first find common range for all elo buckets
        rangeMin, rangeMax = None, None
        for elo in range(self.elo_buckets):
            for Idx in [0, -1]:
                dictList[elo][Idx] = self.depths[elo][Idx].copy()
                # negative depths mean games that end in cdb
                for key, value in list(dictList[elo][Idx].items()):
                    if key < 0 and not negplot:
                        dictList[elo][Idx][-key] = (
                            dictList[elo][Idx].get(-key, 0) + value
                        )
                        del dictList[elo][Idx][key]
                mi, ma = min(dictList[elo][Idx].keys()), max(dictList[elo][Idx].keys())
                if rangeMin is None:
                    rangeMin, rangeMax = mi, ma
                else:
                    rangeMin = min(mi, rangeMin)
                    rangeMax = max(ma, rangeMax)

        numBins = max(1, (rangeMax - rangeMin) // perBin)
        for elo in range(self.elo_buckets):
            for Idx in [0, -1]:
                dateStr = self.date[Idx]
                mi, ma = min(dictList[elo][Idx].keys()), max(dictList[elo][Idx].keys())
                if negplot and mi < 0 and ma > 0:
                    negmax = max([k for k in dictList[elo][Idx].keys() if k < 0])
                    posmin = min([k for k in dictList[elo][Idx].keys() if k > 0])
                    cup = r"$\cup$"
                    rangeStr = f"[{mi}, {negmax}]{cup}[{posmin}, {ma}]"
                else:
                    rangeStr = f"[{mi}, {ma}]"
                noStr = shrink_number_string(sum(dictList[elo][Idx].values()))
                label[Idx] = f"{dateStr}   ({noStr} in {rangeStr})"
                ax[elo].hist(
                    dictList[elo][Idx].keys(),
                    weights=dictList[elo][Idx].values(),
                    range=(rangeMin, rangeMax),
                    bins=numBins,
                    density=densityplot,
                    alpha=0.5,
                    color=color[Idx],
                    edgecolor=edgecolor[Idx],
                    label=label[Idx],
                )
            ax[elo].legend(
                title=self.eloStr[elo],
                fontsize=5,
                title_fontproperties={"size": 6, "weight": "bold"},
            )

            if logplot:
                ax[elo].set_yscale("log")
        prefix = self.prefix.replace("_", r"\_")
        bold = rf"$\bf{{{prefix}}}$"
        fig.suptitle(f"Distribution of cdb exit ply in {bold}.csv.")
        if negplot:
            ax[0].set_title(
                "(A negative ply -d means that a game with d plies ends in cdb.)",
                fontsize=6,
                family="monospace",
            )
        fig.tight_layout(rect=[0, 0, 1, 1.03])

        plt.savefig(self.prefix + ".png", dpi=300)

    def create_timeseries_graph(self, plotStart=0):
        dateData = [datetime.fromisoformat(d + "-01") for d in self.date[plotStart:]]
        depthsData = [[] for _ in range(self.elo_buckets)]
        NoP = [0] * self.elo_buckets

        for bucket in range(self.elo_buckets):
            for i, d in enumerate(self.depths[bucket][plotStart:]):
                ind, n = depth_indicator(d)
                depthsData[bucket].append(ind)
                if i and n != NoP[bucket]:
                    print(
                        f"Warning: NoP changed from {NoP[bucket]} to {n} at {dateData[i]}."
                    )
                NoP[bucket] = n

        fig, ax = plt.subplots()
        yColor, dateColor = "black", "black"
        depthColor = "firebrick"
        if len(dateData) >= 200:
            depthDotSize, depthLineWidth, depthAlpha = 2, 0.7, 0.75
        elif len(dateData) >= 100:
            depthDotSize, depthLineWidth, depthAlpha = 5, 1, 0.75
        else:
            depthDotSize, depthLineWidth, depthAlpha = 15, 1, 0.75
        ax.scatter(
            dateData,
            depthsData[0],
            color=depthColor,
            s=depthDotSize,
            alpha=depthAlpha,
        )
        ax.plot(
            dateData,
            depthsData[0],
            color=depthColor,
            linewidth=depthLineWidth,
            alpha=depthAlpha,
        )
        ax.tick_params(axis="y", labelcolor=depthColor)
        ax.ticklabel_format(axis="y", style="plain")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.setp(
            ax.get_xticklabels(),
            rotation=45,
            ha="right",
            rotation_mode="anchor",
            fontsize=6,
        )
        ax.grid(alpha=0.4, linewidth=0.5)
        fig.suptitle(f"     Progress indicators from {self.prefix}.csv.")
        plt.figtext(0.02, 0.91, depthIndicatorStr, fontsize=9, color=depthColor)
        pair = r"$(e_i, d_i)$"
        infty = r"$d_i=\infty$"
        noStr = str(max(NoP))
        noStr = shrink_number_string(noStr)
        ax.set_title(
            f"     Based on {noStr} (eval, depth) data points {pair}, {infty} for terminal PVs.",
            fontsize=6,
            family="monospace",
        )
        plt.savefig(
            self.prefix + "time" + bool(plotStart) * str(plotStart) + ".png", dpi=300
        )

    def create_depth_graph(self, filename, plotStart=0):
        dateData = [datetime.fromisoformat(d) for d in self.date[plotStart:]]
        depthsAvg = [[] for _ in range(self.elo_buckets)]
        depthsMin = [[] for _ in range(self.elo_buckets)]
        depthsMax = [[] for _ in range(self.elo_buckets)]

        for bucket in range(self.elo_buckets):
            for d in self.depths[bucket][plotStart:]:
                depthsAvg[bucket].append(depth_average(d))
                depthsMax[bucket].append(max(d.keys()))
                depthsMin[bucket].append(min([k for k in d.keys() if k > 0]))

        fig, ax = plt.subplots()
        ax2 = ax.twinx()
        dotSize, lineWidth, alpha = 2, 0.7, 0.75
        ax.scatter(
            dateData,
            depthsAvg[0],
            color="black",
            s=dotSize,
            alpha=alpha,
        )
        ax.scatter(
            dateData,
            depthsMax[0],
            color="silver",
            s=dotSize,
            alpha=alpha,
        )
        ax2.scatter(
            dateData,
            depthsMin[0],
            color="red",
            s=dotSize,
            alpha=alpha,
        )
        ax.plot(
            dateData,
            depthsAvg[0],
            color="black",
            linewidth=lineWidth,
            alpha=alpha,
        )
        ax.tick_params(axis="y", labelcolor="black")
        ax2.tick_params(axis="y", labelcolor="red")
        ax2.ticklabel_format(axis="y", style="plain")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.setp(
            ax.get_xticklabels(),
            rotation=45,
            ha="right",
            rotation_mode="anchor",
            fontsize=6,
        )
        ax.grid(alpha=0.4, linewidth=0.5)
        fig.suptitle(f" Non terminal exit plies from {self.prefix}.csv over time.")
        ybox1 = TextArea(
            "average length",
            textprops=dict(size=9, color="black", rotation=90, ha="left", va="bottom"),
        )
        ybox2 = TextArea(
            "(and max length)",
            textprops=dict(size=6, color="silver", rotation=90, ha="left", va="bottom"),
        )
        ybox = VPacker(children=[ybox2, ybox1], align="center", pad=0, sep=5)
        anchored_ybox = AnchoredOffsetbox(
            loc=8,
            child=ybox,
            pad=0.0,
            frameon=False,
            bbox_to_anchor=(-0.1, 0.3),
            bbox_transform=ax.transAxes,
            borderpad=0.0,
        )
        ax.add_artist(anchored_ybox)
        ax2.set_ylabel("min length", color="red")

        plt.savefig(filename, dpi=300)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plot data stored in e.g. litrack.csv.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "filename",
        nargs="?",
        help="File with cdb exit ply statistics over time.",
        default="litrack.csv",
    )
    parser.add_argument(
        "--logplot",
        action="store_true",
        help="Use logplot for the distribution plot.",
    )
    parser.add_argument(
        "--negplot",
        action="store_true",
        help="Plot exit plies with negative depth separately.",
    )
    parser.add_argument(
        "--densityplot",
        action="store_true",
        help="Plot density in histograms.",
    )
    parser.add_argument(
        "--onlyTime",
        action="store_true",
        help="Create only time evolution graphs.",
    )
    parser.add_argument(
        "--PvLengthPlot",
        help="Optional filename for time series plot of exit ply statistics.",
    )
    args = parser.parse_args()

    prefix, _, _ = args.filename.partition(".")
    data = litrackdata(prefix)
    if not args.onlyTime:
        data.create_distribution_graph(args.logplot, args.negplot, args.densityplot)
    data.create_timeseries_graph()
    if args.PvLengthPlot:
        data.create_depth_graph(args.PvLengthPlot)
