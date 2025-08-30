# app_usage_gui.py — GUI that builds final timeline from EVENTS dump + packages (CSV or XML)
# Requires: pandas (pip install pandas)

import os, re
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from xml.etree import ElementTree as ET

# ----------------- EVENTS PARSER (works with your device) -----------------

TS_RE = re.compile(r'time="(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"')
EV_RE = re.compile(r'type=([A-Z_]+)\s+package=([A-Za-z0-9._]+)')

def parse_events_dump(path: str) -> pd.DataFrame:
    """
    Parse 'dumpsys usagestats' EVENTS-style text and compute:
      - App Launch Count (RESUMED count)
      - Last Time Used (latest event per package)
      - Total Time Used (sum RESUMED -> PAUSED/STOPPED)
    Returns DataFrame with: Package | Last Time Used | Total Time Used | App Launch Count
    """
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

            # Update last time (keep latest)
            if (row["Last Time Used"] is None) or (t > datetime.strptime(row["Last Time Used"], "%Y-%m-%d %H:%M:%S")):
                row["Last Time Used"] = t.strftime("%Y-%m-%d %H:%M:%S")

            if ev == "ACTIVITY_RESUMED":
                row["App Launch Count"] += 1
                open_sessions[pkg] = t

            if ev in ("ACTIVITY_PAUSED", "ACTIVITY_STOPPED") and pkg in open_sessions:
                start = open_sessions.pop(pkg)
                if t > start:
                    row["Total Time Used (s)"] += (t - start).total_seconds()

    # Format total time
    for pkg, row in results.items():
        secs = int(row["Total Time Used (s)"])
        h, m, s = secs//3600, (secs%3600)//60, secs%60
        row["Total Time Used"] = f"{h:02d}:{m:02d}:{s:02d}" if secs > 0 else None
        del row["Total Time Used (s)"]

    df = pd.DataFrame(results.values())
    if not df.empty:
        df = df.sort_values("Last Time Used", ascending=False)
    # Add a placeholder column expected by the merge layout
    df["Last Time Visible"] = None
    return df[["Package","Last Time Used","Last Time Visible","Total Time Used","App Launch Count"]]

# ----------------- PACKAGES PARSER (CSV or XML) -----------------

def _from_ms_or_hex(val):
    if val is None: return None
    s = str(val).strip()
    # int milliseconds (or seconds)
    try:
        n = int(s, 10)
        if n < 10_000_000_000:  # seconds → ms
            n *= 1000
        return datetime.utcfromtimestamp(n/1000).strftime("%Y-%m-%d %H:%M:%S")
    except:
        pass
    # hex milliseconds
    try:
        n = int(s, 16)
        return datetime.utcfromtimestamp(n/1000).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return None

def parse_packages_input(path: str) -> pd.DataFrame:
    """
    Accepts CSV (packages_output.csv-like) OR XML (packages.xml)
    Returns: Package | First Installed | Last Updated | Installer (where available)
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(path)
        # normalise names
        rename = {}
        for c in list(df.columns):
            lc = c.lower().strip()
            if lc in ("package","package name"): rename[c] = "Package"
            elif lc in ("first installed","firstinstalled","first_install_time","first_install"): rename[c] = "First Installed"
            elif lc in ("last updated","lastupdated","last_update_time","last_update"): rename[c] = "Last Updated"
            elif lc in ("installer","installer package","installerpackage"): rename[c] = "Installer"
        df = df.rename(columns=rename)
        keep = [x for x in ["Package","First Installed","Last Updated","Installer"] if x in df.columns]
        if "Package" not in keep:
            raise ValueError("Packages CSV must contain a 'Package' (or 'Package Name') column.")
        return df[keep]

    # XML
    tree = ET.parse(path)
    root = tree.getroot()
    rows = []
    for pkg in root.findall(".//package"):
        name = pkg.attrib.get("name")
        if not name: continue
        ft = pkg.attrib.get("ft") or pkg.attrib.get("firstInstallTime") or pkg.attrib.get("first-install-time")
        ut = pkg.attrib.get("ut") or pkg.attrib.get("lastUpdateTime") or pkg.attrib.get("last-update-time")
        installer = pkg.attrib.get("installer") or pkg.attrib.get("installerPackageName") or pkg.attrib.get("installer-package-name")
        rows.append({
            "Package": name,
            "First Installed": _from_ms_or_hex(ft),
            "Last Updated": _from_ms_or_hex(ut),
            "Installer": installer
        })
    return pd.DataFrame(rows)

# ----------------- MERGE -----------------

def build_final_timeline(usage_df: pd.DataFrame, packages_df: pd.DataFrame) -> pd.DataFrame:
    merged = pd.merge(packages_df, usage_df, on="Package", how="outer")
    # normalise date columns to string
    for col in ["First Installed","Last Updated","Last Time Used","Last Time Visible"]:
        if col in merged.columns:
            merged[col] = pd.to_datetime(merged[col], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
    # desired order
    order = [c for c in [
        "Package","First Installed","Last Updated","Installer",
        "Last Time Used","Last Time Visible","Total Time Used","App Launch Count"
    ] if c in merged.columns]
    merged = merged[order]
    # sort by Last Time Used desc if present
    if "Last Time Used" in merged.columns:
        tmp = pd.to_datetime(merged["Last Time Used"], errors="coerce")
        merged = merged.loc[tmp.sort_values(ascending=False, na_position="last").index]
    return merged

# ----------------- GUI -----------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Android App Usage Timeline — GUI (Events)")
        self.geometry("920x600")

        self.usage_path = tk.StringVar()
        self.packages_path = tk.StringVar()
        self.output_path = tk.StringVar(value="AppUsage_Timeline_Final.csv")

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="x")

        ttk.Label(frm, text="Usage file (events dump, e.g., usagestats_dump.txt):").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.usage_path, width=85).grid(row=0, column=1, padx=6)
        ttk.Button(frm, text="Browse", command=self.browse_usage).grid(row=0, column=2)

        ttk.Label(frm, text="Packages file (packages.xml OR packages_output.csv):").grid(row=1, column=0, sticky="w", pady=(6,0))
        ttk.Entry(frm, textvariable=self.packages_path, width=85).grid(row=1, column=1, padx=6, pady=(6,0))
        ttk.Button(frm, text="Browse", command=self.browse_packages).grid(row=1, column=2, pady=(6,0))

        ttk.Label(frm, text="Output CSV:").grid(row=2, column=0, sticky="w", pady=(6,0))
        ttk.Entry(frm, textvariable=self.output_path, width=85).grid(row=2, column=1, padx=6, pady=(6,0))
        ttk.Button(frm, text="Save As", command=self.browse_output).grid(row=2, column=2, pady=(6,0))

        btns = ttk.Frame(self, padding=(12,0))
        btns.pack(fill="x")
        ttk.Button(btns, text="Generate Timeline", command=self.generate).pack(side="left")
        ttk.Button(btns, text="Quit", command=self.destroy).pack(side="right")

        self.tree = ttk.Treeview(self, show="headings")
        self.tree.pack(fill="both", expand=True, padx=12, pady=12)

    def browse_usage(self):
        path = filedialog.askopenfilename(title="Select usage dump (TXT)", filetypes=[("All files","*.*")])
        if path: self.usage_path.set(path)

    def browse_packages(self):
        path = filedialog.askopenfilename(title="Select packages file (CSV or XML)", filetypes=[("All files","*.*")])
        if path: self.packages_path.set(path)

    def browse_output(self):
        path = filedialog.asksaveasfilename(title="Save final CSV as...", defaultextension=".csv",
                                            filetypes=[("CSV files","*.csv"), ("All files","*.*")])
        if path: self.output_path.set(path)

    def generate(self):
        try:
            if not self.usage_path.get():
                messagebox.showerror("Error", "Please select the events usage dump (usagestats_dump.txt).")
                return
            if not self.packages_path.get():
                messagebox.showerror("Error", "Please select packages.xml or packages_output.csv.")
                return

            usage_df = parse_events_dump(self.usage_path.get())
            if usage_df.empty:
                messagebox.showwarning("No Events Parsed",
                    "Could not extract any events. Make sure your dump contains lines like:\n"
                    'time="YYYY-MM-DD HH:MM:SS" type=ACTIVITY_RESUMED package=com.example')
            packages_df = parse_packages_input(self.packages_path.get())

            final_df = build_final_timeline(usage_df, packages_df)

            out = self.output_path.get() or "AppUsage_Timeline_Final.csv"
            final_df.to_csv(out, index=False, encoding="utf-8")
            messagebox.showinfo("Success", f"Timeline saved to:\n{out}")
            self.preview(final_df)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def preview(self, df: pd.DataFrame):
        # clear
        for c in self.tree.get_children():
            self.tree.delete(c)
        cols = list(df.columns)
        self.tree["columns"] = cols
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=160, anchor="w")
        for _, row in df.head(60).iterrows():
            self.tree.insert("", "end", values=[row.get(c, "") for c in cols])

if __name__ == "__main__":
    # DPI tweak for some Windows screens
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = App()
    app.mainloop()
