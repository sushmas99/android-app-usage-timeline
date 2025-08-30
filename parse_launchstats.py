import re

def extract_utf16_package_names(data):
    # Look for UTF-16LE patterns that resemble Android package names
    strings = []
    for i in range(len(data) - 4):
        try:
            chunk = data[i:i+100]  # Read ahead
            decoded = chunk.decode('utf-16le', errors='ignore')
            if 'com.' in decoded:
                pkg = decoded.split('\x00')[0]  # stop at null
                if '.' in pkg and len(pkg) < 100:
                    strings.append(pkg)
        except:
            continue
    return list(set(strings))  # deduplicate

def main():
    with open("LaunchStats.data", "rb") as f:
        data = f.read()

    packages = extract_utf16_package_names(data)

    if packages:
        print("🟢 Detected Package Names:")
        for i, pkg in enumerate(packages, 1):
            print(f"{i}. {pkg}")
    else:
        print("❌ No package names detected.")

    print(f"\n✅ Total Detected: {len(packages)} apps")

if __name__ == "__main__":
    main()

