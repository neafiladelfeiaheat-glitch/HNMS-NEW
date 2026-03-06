from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import json
import os
import sys

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.accept_insecure_certs = True

driver = webdriver.Chrome(options=chrome_options)

try:
    print("Εκκίνηση... Ανίχνευση χάρτη Leaflet (Zero-Menu Method)")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(25) # Δίνουμε χρόνο στον χάρτη να "γεννήσει" τις πινέζες

    # ΤΟ ΑΠΟΛΥΤΟ SCRIPT: Ψάχνει όλα τα Layers του χάρτη και τραβάει τα IDs
    js_sniffer = """
    var stations = [];
    try {
        var mapContainer = document.querySelector('.leaflet-container');
        var mapObj = null;
        
        // Ψάχνουμε το εσωτερικό αντικείμενο του χάρτη
        for (let key in mapContainer) {
            if (key.startsWith('__leaflet_')) {
                mapObj = mapContainer[key];
                if (mapObj._map) mapObj = mapObj._map;
                break;
            }
        }

        if(mapObj) {
            mapObj.eachLayer(function(layer) {
                if(layer._popup && layer._popup._content) {
                    var content = layer._popup._content;
                    // Ψάχνουμε τη συνάρτηση selectStation(ID) μέσα στο popup
                    var idMatch = content.match(/selectStation\\((\\d+)\\)/);
                    var nameMatch = content.match(/<b>(.*?)<\\/b>/) || content.match(/<h[1-6]>(.*?)<\\/h[1-6]>/);
                    
                    if(idMatch) {
                        stations.append({
                            id: idMatch[1],
                            name: (nameMatch ? nameMatch[1] : "Station_" + idMatch[1]).trim().replace(/ /g, "_")
                        });
                    }
                }
            });
        }
    } catch(e) { return "ERROR: " + e.message; }
    return stations;
    """
    
    stations_data = driver.execute_script(js_sniffer)
    
    # Αν το sniffer αποτύχει, δοκιμάζουμε το plan B: "Regex στο Page Source"
    if not stations_data or isinstance(stations_data, str):
        print("Το sniffer απέτυχε, πάμε σε Hard-Coding Regex...")
        page_source = driver.page_source
        import re
        # Ψάχνουμε μοτίβα του στυλ selectStation(123) και το όνομα δίπλα
        found = re.findall(r'selectStation\((\d+)\)', page_source)
        stations_data = [{"id": s_id, "name": f"Station_{s_id}"} for s_id in set(found)]

    if not stations_data:
        print("ΣΦΑΛΜΑ: Ούτε ο χάρτης ούτε ο κώδικας έδωσαν σταθμούς.")
        sys.exit(1)

    with open('stations.json', 'w', encoding='utf-8') as f:
        json.dump(stations_data, f, ensure_ascii=False)
    
    print(f"ΕΠΙΤΥΧΙΑ: Βρέθηκαν {len(stations_data)} σταθμοί!")

except Exception as e:
    print(f"Crash: {e}")
    sys.exit(1)
finally:
    driver.quit()
