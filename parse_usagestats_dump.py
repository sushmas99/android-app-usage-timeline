import re
import pandas as pd
from datetime import datetime

def parse_usagestats_dump(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()

    # Regex pattern for new format lines
    pattern = r'package=(\S+)\s+totalTimeUsed="([^"]+)"\s+lastTimeUsed="([^"]+)"\s+' \
              r'totalTimeVisible="([^"]+)"\s+lastTimeVisible="([^"]+)"\s+' \
              r'totalTimeFS="([^"]+)"\s+lastTimeFS="([^"]+)"\s+appLaunchCount=(\d+)'

    matches = re.findall(pattern, text)

    records = []

    for pkg, ttu, ltu, ttv, ltv, tfs, lfs, launch_count in matches:
        try:
            ltu_dt = datetime.strptime(ltu, "%Y-%m-%d %H:%M:%S")
            ltv_dt = datetime.strptime(ltv, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

        records.append({
            "Package": pkg,
            "Last Time Used": ltu_dt,
            "Last Time Visible": ltv_dt,
            "Total Time Used": ttu,
            "App Launch Count": int(launch_count)
        })

    df = pd.DataFrame(records)
    df = df.sort_values("Last Time Used")

    # Save to CSV
    df.to_csv("UsageTimeline_Full.csv", index=False)
    print("✅ Timeline saved to 'UsageTimeline_Full.csv'")
    print(df.tail(10))  # Preview

# Run the function
parse_usagestats_dump("usagestats_dump.txt")


