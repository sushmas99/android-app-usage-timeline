# events_to_daily_heatmap.py
# Build a launches-per-day heatmap from usagestats EVENT dump
# Usage:
#   python events_to_daily_heatmap.py usagestats_dump.txt --top 12
# Output:
#   daily_launch_counts.csv + a PNG figure

import re, sys, argparse
from datetime import datetime
from collections import defaultdict, Counter

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

TS_RE = re.compile(r'time="(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"')
EV_RE = re.compile(r'type=([A-Z_]+)\s+package=([A-Za-z0-9._]+)')

def parse_args():
    ap = argparse.ArgumentParser(description="Heatmap of app launches per day")
    ap.add_argument("dump", help="usagestats events dump (TXT)")
    ap.add_argument("--top", type=int, default=10, help="Top-N apps by launches to show (default 10)")
    ap.add_argument("--out", default="daily_launch_counts.csv", help="CSV output filename")
    ap.add_argument("--fig", default="launch_heatmap.png", help="PNG figure output")
    return ap.parse_args()

def main():
    args = parse_args()

    # Count RESUMED per (date, package)
    day_pkg = Counter()

    with open(args.dump, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            ts_m = TS_RE.search(line)
            ev_m = EV_RE.search(line)
            if not ts_m or not ev_m:
                continue
            ev = ev_m.group(1)
            if ev != "ACTIVITY_RESUMED":
                continue
            pkg = ev_m.group(2)
            dt = datetime.strptime(ts_m.group(1), "%Y-%m-%d %H:%M:%S")
            day = dt.date().isoformat()
            day_pkg[(day, pkg)] += 1

    if not day_pkg:
        print("No ACTIVITY_RESUMED events found. Open some apps, regenerate dump, and try again.")
        sys.exit(1)

    # Build DataFrame
    rows = [{"Date": d, "Package": p, "Launches": c} for (d, p), c in day_pkg.items()]
    df = pd.DataFrame(rows)
    # Top-N apps overall
    top_apps = (df.groupby("Package")["Launches"].sum()
                  .sort_values(ascending=False).head(args.top).index.tolist())
    df = df[df["Package"].isin(top_apps)]

    # Pivot to Date × Package
    pivot = df.pivot_table(index="Date", columns="Package", values="Launches", aggfunc="sum", fill_value=0)
    pivot = pivot.sort_index()  # date ascending

    # Save CSV
    pivot.to_csv(args.out, index=True)
    print(f"✅ Saved daily launch counts to {args.out}")

    # Plot heatmap (matplotlib only; no seaborn)
    fig, ax = plt.subplots(figsize=(max(8, len(top_apps)*0.7), max(5, len(pivot.index)*0.4)))
    im = ax.imshow(pivot.values, aspect="auto", interpolation="nearest")  # default colormap

    # Axis labels
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_title("App launches per day (Top {} apps)".format(len(top_apps)))
    ax.set_xlabel("App package")
    ax.set_ylabel("Date")

    # Add a simple colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Launches")

    plt.tight_layout()
    plt.savefig(args.fig, dpi=200)
    print(f"✅ Saved heatmap to {args.fig}")
    plt.show()

if __name__ == "__main__":
    main()
