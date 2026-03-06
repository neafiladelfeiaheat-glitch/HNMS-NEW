import json
import sys

# Η Hardcoded λίστα ασφαλείας - Διορθωμένη 100%
fallback_stations = [
    {"id": "68", "name": "ELLINIKO"},
    {"id": "119", "name": "KASOS"},
    {"id": "106", "name": "SPARTI"},
    {"id": "116", "name": "IRAKLEIO"},
    {"id": "34", "name": "THESSALONIKI_MIKRA"},
    {"id": "12", "name": "ALEXANDROUPOLI"},
    {"id": "84", "name": "KALAMATA"},
    {"id": "97", "name": "KYTHIRA"},
    {"id": "52", "name": "LARISA"},
    {"id": "124", "name": "TYMPAKI"},
    {"id": "111", "name": "RODOS"},
    {"id": "74", "name": "TANAGRA"},
    {"id": "59", "name": "ANCHIALOS"},
    {"id": "46", "name": "KERKYRA"},
    {"id": "118", "name": "KARPATHOS"},
    {"id": "115", "name": "SOUDA"},
    {"id": "113", "name": "MILOS"},
    {"id": "114", "name": "NAXOS"},
    {"id": "102", "name": "TRIPOLI"},
    {"id": "80", "name": "ARAXOS"},
    {"id": "48", "name": "AKTIO"},
    {"id": "28", "name": "LEMNOS"},
    {"id": "25", "name": "MYTILINI"},
    {"id": "22", "name": "SKIATHOS"},
    {"id": "23", "name": "SKYROS"},
    {"id": "15", "name": "KAVALA"},
    {"id": "18", "name": "CHIOS"}
]

try:
    with open('stations.json', 'w', encoding='utf-8') as f:
        json.dump(fallback_stations, f, ensure_ascii=False)
    print(f"ΕΠΙΤΥΧΙΑ: Δημιουργήθηκε λίστα με {len(fallback_stations)} σταθμούς.")
except Exception as e:
    print(f"Σφάλμα: {e}")
    sys.exit(1)
