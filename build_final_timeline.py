import pandas as pd

# Load the usage stats CSV
usage_df = pd.read_csv("UsageTimeline_Full.csv")

# Load the packages install data
packages_df = pd.read_csv("packages_output.csv")

# Create "Last Used" events
usage_events = usage_df[['Package', 'Last Time Used', 'App Launch Count']].copy()
usage_events = usage_events.rename(columns={
    'Last Time Used': 'Timestamp',
    'App Launch Count': 'Details'
})
usage_events['Event Type'] = 'Last Used'
usage_events['Details'] = 'Launch Count: ' + usage_events['Details'].astype(str)

# Create "Last Visible" events
visible_events = usage_df[['Package', 'Last Time Visible', 'Total Time Used']].copy()
visible_events = visible_events.rename(columns={
    'Last Time Visible': 'Timestamp',
    'Total Time Used': 'Details'
})
visible_events['Event Type'] = 'Last Visible'
visible_events['Details'] = 'Used for: ' + visible_events['Details']

# Create "Installed" events from packages
install_events = packages_df[['Package Name', 'First Installed']].copy()
install_events = install_events.rename(columns={
    'Package Name': 'Package',
    'First Installed': 'Timestamp'
})
install_events['Event Type'] = 'Installed'
install_events['Details'] = 'From packages.xml'

# Combine all 3 types of events
final_timeline = pd.concat([usage_events, visible_events, install_events], ignore_index=True)

# Convert Timestamp to datetime
final_timeline['Timestamp'] = pd.to_datetime(final_timeline['Timestamp'], errors='coerce')

# Remove rows with invalid timestamps
final_timeline = final_timeline.dropna(subset=['Timestamp'])

# Sort by time
final_timeline = final_timeline.sort_values(by='Timestamp')

# Save to CSV
final_timeline.to_csv("AppUsage_Timeline_Final.csv", index=False)
print("✅ Final timeline saved to 'AppUsage_Timeline_Final.csv'")
