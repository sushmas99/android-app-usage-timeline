import xml.etree.ElementTree as ET
from datetime import datetime
import csv

def parse_hex_timestamp(hex_str):
    try:
        return datetime.fromtimestamp(int(hex_str, 16) / 1000).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "Invalid Timestamp"

def parse_packages_xml(xml_path, csv_output="packages_output.csv"):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    data = []

    for pkg in root.findall('package'):
        name = pkg.attrib.get('name', 'N/A')
        ft_raw = pkg.attrib.get('ft', '0')
        ut_raw = pkg.attrib.get('ut', '0')
        installer = pkg.attrib.get('installer', 'N/A')
        uid = int(pkg.attrib.get('userId', '0'))

        # Only keep user-installed apps (UID >= 10000)
        if uid < 10000:
            continue

        # Permissions (if any)
        permissions = [perm.attrib['name'] for perm in pkg.findall('perms/item')]
        permission_str = ', '.join(permissions) if permissions else 'None'

        ft = parse_hex_timestamp(ft_raw)
        ut = parse_hex_timestamp(ut_raw)

        data.append({
            'Package Name': name,
            'First Installed': ft,
            'Last Updated': ut,
            'Installer': installer,
            'Permissions': permission_str,
            'UID': uid
        })

    # Print nicely
    print(f"{'Package Name':<50} {'First Installed':<25} {'Last Updated':<25} {'Installer':<20}")
    print("-" * 120)
    for row in data:
        print(f"{row['Package Name']:<50} {row['First Installed']:<25} {row['Last Updated']:<25} {row['Installer']:<20}")

    # Save to CSV
    with open(csv_output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    print(f"\n✅ Saved output to: {csv_output}")

if __name__ == "__main__":
    xml_file = "packages.xml"  # Must be in same folder
    parse_packages_xml(xml_file)
