📱 Android App Usage Timeline Tool

This project provides an open-source forensic tool to extract, parse, and visualize Android app usage timelines from usagestats and packages.xml.
It automates the process of reconstructing app usage behaviour for criminal profiling and digital investigations.

✨ Features:

📂 Extracts app installation data from packages.xml or packages_output.csv

🕒 Parses app usage sessions from dumpsys usagestats --history

🔗 Merges installation + usage data into a single timeline CSV

🖥️ GUI for non-technical users (browse → generate → export CSV)

📊 Visualizations:

Bar Chart: for launch counts

Heatmap: daily launches per app

Gantt chart: usage sessions across a chosen day

🛠️ Requirements

Python 3.9+

Packages:

pip install pandas matplotlib


ADB (Android Debug Bridge) installed in your system PATH

📤 Data Extraction

Connect your rooted (or debug-enabled) Android device.

Generate usage dump:

adb shell dumpsys usagestats --history > usagestats_dump.txt


Extract packages list:

adb pull /data/system/packages.xml ./packages.xml


(if /data/system/packages.xml not accessible, use a pre-extracted packages_output.csv)

▶️ Usage
1) Run the GUI
python app_usage_gui.py


Select usagestats_dump.txt

Select packages.xml or packages_output.csv

Click Generate Timeline → outputs AppUsage_Timeline_Final.csv

2) Visualizations
Heatmap (launches per day × app)
python events_to_daily_heatmap.py usagestats_dump.txt --top 12


Outputs:

daily_launch_counts.csv

launch_heatmap.png

Gantt Chart (sessions for one day)
python events_to_gantt.py usagestats_dump.txt --day 2025-08-30 --top 10

🔒 Disclaimer

This tool is intended for academic and forensic research purposes only.
Do not run on devices without proper legal authorisation.

📚 References

Kwon et al. (2021). Mobile usage patterns for profiling.

Grover (2013). Automated data collection for Android.

Ogundiran et al. (2024). Timeline analysis of Telegram artefacts.

🚀 Future Work

Extend support for non-rooted devices via adb statsd APIs

Add session clustering for behavioural profiling

Integrate a web dashboard for interactive timeline browsing

📧 Maintainer: Sushma Siddaraju
