# events_to_gantt.py
# Build a Gantt-style chart of usage sessions (RESUMED -> PAUSED/STOPPED) for a chosen day
# Usage:
#   python events_to_gantt.py usagestats_dump.txt --day 2025-08-30 --top 10
# Output:
#   gantt_<day>.png + a sessions CSV

import re, sys, argparse
from datetime import datetime, timedelta
from collections import defaultdict

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MinuteLocator, HourLocator

TS_RE = re.compile(r'time="(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"')
EV_RE = re.compile(r'type=([A-Z_]+)\s+package=([A-Za-z0-9._]+)')

def parse_args():
    ap = argparse.ArgumentParser(description="Gantt of app sessions for a day")
    ap.add_argument("dump", help="usagestats events dump (TXT)")
    ap.add_argument("--day", help="YYYY-MM-DD (default: latest day found in dump)")
    ap.add_argument("--top", type=int, default=10, help="Top-N apps by total session time")
    ap.add_argument("--fig", help="Output PNG filename (optional)")
    ap.add_argument("--out", default=None, help="Sessions CSV filename (optional)")
    return ap.parse_args()

def main():
    args = parse_args()

    # Parse all events
    events = []  # (dt, ev, pkg)
    with open(args.dump, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            ts_m = TS_RE.search(line)
            ev_m = EV_RE.search(line)
            if not ts_m or not ev_m:
                continue
            dt = datetime.strptime(ts_m.group(1), "%Y-%m-%d %H:%M:%S")
            ev = ev_m.group(1)
            pkg = ev_m.group(2)
            if ev not in ("ACTIVITY_RESUMED","ACTIVITY_PAUSED","ACTIVITY_STOPPED"):
                continue
            events.append((dt, ev, pkg))

    if not events:
        print("No relevant events found.")
        sys.exit(1)

    # Determine target day
    dates = sorted({e[0].date() for e in events})
    target_day = datetime.strptime(args.day, "%Y-%m-%d").date() if args.day else dates[-1]
    start_day = datetime.combine(target_day, datetime.min.time())
    end_day = start_day + timedelta(days=1)

    # Build sessions (start = RESUMED, end = next PAUSED/STOPPED)
    sessions = defaultdict(list)  # pkg -> list of (start, end)
    open_start = {}               # pkg -> start_dt

    for dt, ev, pkg in sorted(events):
        if dt.date() < target_day or dt >= end_day:
            # still allow a session that started earlier but ends today
            if ev in ("ACTIVITY_PAUSED","ACTIVITY_STOPPED") and pkg in open_start:
                st = open_start.pop(pkg)
                if st < end_day and dt >= start_day:
                    s = max(st, start_day)
                    e = min(dt, end_day)
                    if e > s:
                        sessions[pkg].append((s, e))
            continue

        if ev == "ACTIVITY_RESUMED":
            open_start[pkg] = dt
        elif ev in ("ACTIVITY_PAUSED","ACTIVITY_STOPPED"):
            if pkg in open_start:
                st = open_start.pop(pkg)
                # clip to the day window
                s = max(st, start_day)
                e = min(dt, end_day)
                if e > s:
                    sessions[pkg].append((s, e))

    # close any still-open sessions at end of day
    for pkg, st in list(open_start.items()):
        s = max(st, start_day)
        e = end_day
        if e > s:
            sessions[pkg].append((s, e))

    # Compute totals and select top apps
    totals = {pkg: sum((e - s).total_seconds() for s, e in sess) for pkg, sess in sessions.items()}
    top_pkgs = [p for p, _ in sorted(totals.items(), key=lambda x: x[1], reverse=True)[:args.top]]

    # Build DataFrame of sessions for CSV
    rows = []
    for pkg in top_pkgs:
        for s, e in sessions.get(pkg, []):
            rows.append({"Package": pkg, "Start": s, "End": e, "Duration_s": (e - s).total_seconds()})
    sess_df = pd.DataFrame(rows).sort_values(["Package","Start"])
    if args.out is None:
        args.out = f"sessions_{target_day.isoformat()}.csv"
    sess_df.to_csv(args.out, index=False)
    print(f"✅ Saved sessions CSV to {args.out}")

    # Plot Gantt using broken_barh
    fig, ax = plt.subplots(figsize=(12, max(5, len(top_pkgs)*0.6)))
    y_ticks, y_labels = [], []
    y = 10
    for pkg in top_pkgs:
        segs = []
        for _, row in sess_df[sess_df["Package"] == pkg].iterrows():
            start = pd.to_datetime(row["Start"]).to_pydatetime()
            end = pd.to_datetime(row["End"]).to_pydatetime()
            segs.append( (start, end - start) )
        # convert to matplotlib's float dates
        segs_conv = [(pd.to_datetime(s).to_pydatetime(), d) for s, d in segs]
        # matplotlib broken_barh expects numbers, so convert using date2num
        from matplotlib.dates import date2num
        segs_num = [(date2num(s), d.total_seconds()/86400.0) for s, d in segs_conv]  # duration in days

        ax.broken_barh(segs_num, (y, 8))
        y_ticks.append(y + 4)
        y_labels.append(pkg)
        y += 12

    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.xaxis.set_major_locator(HourLocator(interval=1))
    ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    ax.set_xlim(pd.to_datetime(start_day), pd.to_datetime(end_day))
    ax.set_title(f"App usage sessions on {target_day.isoformat()} (Top {len(top_pkgs)} by duration)")
    ax.set_xlabel("Time of day")
    ax.set_ylabel("Apps")

    plt.tight_layout()
    fig_name = args.fig or f"gantt_{target_day.isoformat()}.png"
    plt.savefig(fig_name, dpi=200)
    print(f"✅ Saved Gantt chart to {fig_name}")
    plt.show()

if __name__ == "__main__":
    main()

