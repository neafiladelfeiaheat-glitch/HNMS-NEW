import json
import sys

# Η οριστική λίστα IDs από τη βάση της ΕΜΥ
stations = [
    {"id": "68", "name": "ELLINIKO"},
    {"id": "119", "name": "KASOS"},
    {"id": "106", "name": "SPARTI"},
    {"id": "116", "name": "IRAKLEIO"},
    {"id": "34", "name": "THESSALONIKI_MIKRA"},
    {"id": "84", "name": "KALAMATA"},
    {"id": "111", "name": "RODOS"},
    {"id": "52", "name": "LARISA"},
    {"id": "124", "name": "TYMPAKI"},
    {"id": "115", "name": "SOUDA"},
    {"id": "46", "name": "KERKYRA"},
    {"id": "12", "name": "ALEXANDROUPOLI"}
]

try:
    with open('stations.json', 'w', encoding='utf-8') as f:
        json.dump(stations, f, ensure_ascii=False)
    print("Λίστα σταθμών έτοιμη.")
except Exception as e:
    sys.exit(1)
