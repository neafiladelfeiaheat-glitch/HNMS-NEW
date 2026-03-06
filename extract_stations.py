from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import json
import os

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
    print("Εκκίνηση... Εξαγωγή Λίστας Σταθμών...")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(12) 

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
                var matchId = content.match(/selectStation\s*\((\d+)\)/); // Βρίσκει το ID
                var tempDiv = document.createElement('div');
                tempDiv.innerHTML = content;
                var text = tempDiv.textContent || tempDiv.innerText;
                var name = text.split('\\n')[0].trim(); // Βρίσκει το όνομα
                
                if (matchId && name) {
                    stations.push({
                        id: matchId[1],
                        name: name.replace(' ', '_').replace('/', '_')
                    });
                }
            }
        });
        return stations;
    } catch(e) { return null; }
    """
    
    stations_data = driver.execute_script(js_get_leaflet_data)
    
    if stations_data:
        # Προσθέτουμε το Ελληνικό (συνήθως ID 68 ή 104) χειροκίνητα
        stations_data.append({"id": "68", "name": "ΕΛΛΗΝΙΚΟ"}) 
        # Αφαίρεση διπλοτύπων
        seen = set()
        unique_stations = []
        for s in stations_data:
            if s['id'] not in seen:
                seen.add(s['id'])
                unique_stations.append(s)
                
        # Σώζουμε σε JSON αρχείο
        with open('stations.json', 'w', encoding='utf-8') as f:
            json.dump(unique_stations, f, ensure_ascii=False, indent=4)
        print(f"ΕΠΙΤΥΧΙΑ: Εξήχθησαν {len(unique_stations)} σταθμοί στο stations.json")
    else:
        print("Σφάλμα: Δεν βρέθηκαν σταθμοί.")

except Exception as e:
    print(f"Σφάλμα κατά την εξαγωγή: {e}")
finally:
    driver.quit()
