# events_parser.py
import re
import pandas as pd
from datetime import datetime

TS_RE = re.compile(r'time="(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"')
EV_RE = re.compile(r'type=([A-Z_]+)\s+package=([A-Za-z0-9._]+)')

def parse_events(path):
    results = {}
    open_sessions = {}

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            ts_m = TS_RE.search(line)
            ev_m = EV_RE.search(line)
            if not ts_m or not ev_m:
                continue

            t = datetime.strptime(ts_m.group(1), "%Y-%m-%d %H:%M:%S")
            ev = ev_m.group(1)
            pkg = ev_m.group(2)

            row = results.setdefault(pkg, {
                "Package": pkg,
                "Last Time Used": None,
                "Total Time Used (s)": 0,
                "App Launch Count": 0
            })

            # Update last time
            if row["Last Time Used"] is None or t > datetime.strptime(row["Last Time Used"], "%Y-%m-%d %H:%M:%S"):
                row["Last Time Used"] = t.strftime("%Y-%m-%d %H:%M:%S")

            if ev == "ACTIVITY_RESUMED":
                row["App Launch Count"] += 1
                open_sessions[pkg] = t

            if ev in ("ACTIVITY_PAUSED", "ACTIVITY_STOPPED") and pkg in open_sessions:
                start = open_sessions.pop(pkg)
                if t > start:
                    row["Total Time Used (s)"] += (t - start).total_seconds()

    # Format total time used
    for pkg, row in results.items():
        secs = int(row["Total Time Used (s)"])
        h, m, s = secs//3600, (secs%3600)//60, secs%60
        row["Total Time Used"] = f"{h:02d}:{m:02d}:{s:02d}"
        del row["Total Time Used (s)"]

    df = pd.DataFrame(results.values())
    df = df.sort_values("Last Time Used", ascending=False)
    return df

if __name__ == "__main__":
    df = parse_events("usagestats_dump.txt")
    print(df.head(20))
    df.to_csv("usage_from_events.csv", index=False)
    print("✅ Saved usage_from_events.csv")
