import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("AppUsage_Timeline_Final.csv")
launch_df = df[df['Event Type'] == 'Last Used']

# Sum launch counts per app
launch_df['Count'] = launch_df['Details'].str.extract(r'(\d+)').astype(int)
top_apps = launch_df.groupby('Package')['Count'].sum().sort_values(ascending=False).head(10)

# Plot
top_apps.plot(kind='barh', title='Top 10 Apps by Launch Count', figsize=(10,6))
plt.xlabel("Launch Count")
plt.ylabel("App Package")
plt.tight_layout()
plt.show()
