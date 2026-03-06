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
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)

try:
    print("Εκκίνηση Extractor...")
    driver.get("https://www.emy.gr/hnms-stations")
    # Αυξάνουμε την αναμονή στα 20 δευτερόλεπτα για σιγουριά
    time.sleep(20) 

    js_get_leaflet_data = """
    try {
        var container = document.querySelector('.leaflet-container');
        if(!container) return null;
        var map = null;
        for (var key in container) {
            if (key.startsWith('__leaflet_')) {
                map = container[key];
                if (map._map) map = map._map;
                break;
            }
        }
        if(!map) return null;
        
        var stations = [];
        map.eachLayer(function(layer) {
            if(layer._popup && typeof layer._popup._content === 'string') {
                var content = layer._popup._content;
                var matchId = content.match(/selectStation\\s*\\((\\d+)\\)/);
                var tempDiv = document.createElement('div');
                tempDiv.innerHTML = content;
                var text = tempDiv.textContent || tempDiv.innerText;
                var name = text.split('\\n')[0].trim();
                
                if (matchId && name) {
                    stations.push({
                        id: matchId[1],
                        name: name.replace(/[^a-zA-Z0-9α-ωΑ-Ω]/g, '_')
                    });
                }
            }
        });
        return stations;
    } catch(e) { return null; }
    """
    
    stations_data = driver.execute_script(js_get_leaflet_data)
    
    if not stations_data or len(stations_data) == 0:
        print("ΣΦΑΛΜΑ: Δεν βρέθηκαν σταθμοί στον χάρτη!")
        sys.exit(1) # Αναγκάζουμε το Workflow να σταματήσει εδώ

    # Προσθήκη Ελληνικού
    stations_data.append({"id": "68", "name": "ELLINIKO"})
    
    seen = set()
    unique_stations = []
    for s in stations_data:
        if s['id'] not in seen:
            seen.add(s['id'])
            unique_stations.append(s)

    with open('stations.json', 'w', encoding='utf-8') as f:
        json.dump(unique_stations, f, ensure_ascii=False)
    
    print(f"ΕΠΙΤΥΧΙΑ: {len(unique_stations)} σταθμοί έτοιμοι.")

except Exception as e:
    print(f"Crash: {e}")
    sys.exit(1)
finally:
    driver.quit()
