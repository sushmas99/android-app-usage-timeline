import xml.etree.ElementTree as ET
from datetime import datetime

import xml.etree.ElementTree as ET
from datetime import datetime

def parse_hex_timestamp(hex_str):
    try:
        return datetime.fromtimestamp(int(hex_str, 16) / 1000).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "Invalid Timestamp"

def parse_packages_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    print(f"{'Package Name':<50} {'First Installed':<25} {'Last Updated':<25} {'Installer':<25}")
    print("-" * 130)

    for pkg in root.findall('package'):
        name = pkg.attrib.get('name', 'N/A')
        ft_raw = pkg.attrib.get('ft', '0')
        ut_raw = pkg.attrib.get('ut', '0')
        installer = pkg.attrib.get('installer', 'N/A')

        ft = parse_hex_timestamp(ft_raw)
        ut = parse_hex_timestamp(ut_raw)

        print(f"{name:<50} {ft:<25} {ut:<25} {installer:<25}")

if __name__ == "__main__":
    xml_file = "packages.xml"
    parse_packages_xml(xml_file)
