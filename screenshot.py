from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
from datetime import datetime

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,3000')

# Η Ασπίδα SSL για να περνάμε τον τοίχο της ΕΜΥ
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.accept_insecure_certs = True

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)

try:
    print("Εκκίνηση: Ανθρώπινο Χέρι & Δυναμική Σάρωση ΟΛΩΝ των Σταθμών...")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(15)

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(f"screenshots/{today}", exist_ok=True)

    # 1. Καθαρισμός ενοχλητικών παραθύρων/cookies
    driver.execute_script("""
        document.querySelectorAll('*').forEach(el => {
            var s = window.getComputedStyle(el);
            if(s.position === 'fixed' || s.position === 'sticky' || el.id.includes('cookie')) el.remove();
        });
    """)
    time.sleep(2)

    # 2. ΕΞΑΓΩΓΗ ΟΛΩΝ ΤΩΝ ΣΤΑΘΜΩΝ ΑΠΟ ΤΟΝ ΧΑΡΤΗ
    js_get_all_stations = """
    var container = document.querySelector('.leaflet-container');
    if(!container) return [];
    var map = null;
    for (var key in container) {
        if (key.startsWith('__leaflet_')) {
            map = container[key];
            if (map._map) map = map._map;
            break;
        }
    }
    if(!map) return [];
    
    var stations = [];
    map.eachLayer(function(layer) {
        if(layer._popup && typeof layer._popup._content === 'string') {
            var tempDiv = document.createElement('div');
            tempDiv.innerHTML = layer._popup._content;
            var text = tempDiv.textContent || tempDiv.innerText;
            var lines = text.split('\\n');
            for(var i=0; i<lines.length; i++) {
                if(lines[i].trim().length > 2) {
                    stations.push(lines[i].trim());
                    break;
                }
            }
        }
    });
    return [...new Set(stations)];
    """
    all_stations = driver.execute_script(js_get_all_stations)
    
    if not all_stations:
        print("Προειδοποίηση: Δεν βρέθηκαν σταθμοί δυναμικά. Εκκίνηση μόνο με Ελληνικό.")
        all_stations = ["ΕΛΛΗΝΙΚΟ"]
    else:
        print(f"ΒΡΕΘΗΚΑΝ {len(all_stations)} ΣΤΑΘΜΟΙ! Ξεκινάει η μαζική σάρωση.")

    # 3. ΣΑΡΩΣΗ ΕΝΑΝ-ΕΝΑΝ
    for idx, station in enumerate(all_stations):
        print(f"\n[{idx+1}/{len(all_stations)}] Επεξεργασία: {station}")
        try:
            # Ανοίγουμε την πινέζα σιωπηλά για να μην έχουμε επικαλύψεις γραφικών
            js_open_pin = f"""
            var container = document.querySelector('.leaflet-container');
            var map = null;
            for (var key in container) {{
                if (key.startsWith('__leaflet_')) {{ map = container[key]; if (map._map) map = map._map; break; }}
            }}
            var found = false;
            map.eachLayer(function(layer) {{
                if(layer._popup && typeof layer._popup._content === 'string') {{
                    if(layer._popup._content.includes('{station}')) {{
                        layer.fire('click');
                        found = true;
                    }}
                }}
            }});
            return found;
            """
            driver.execute_script(js_open_pin)
            time.sleep(3) # Χρόνος για να κατέβουν τα δεδομένα του σταθμού

            # Σκρολ ακριβώς πάνω στο διάγραμμα
            try:
                chart_container = driver.find_element(By.CSS_SELECTOR, ".highcharts-container")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chart_container)
                time.sleep(4)
            except:
                print(f"[{station}] Δεν βρέθηκε διάγραμμα.")
                continue

            # Υπολογισμός των ακριβών pixels (X, Y) του Max και Min
            js_get_pixels = """
            var chart = Highcharts.charts.find(c => c && c.series && c.series[0].points);
            if (!chart) return null;
            var points = chart.series[0].points;
            var maxPt = null, minPt = null;
            
            for(var i=0; i<points.length; i++) {
                if(points[i].y !== null) {
                    if(maxPt === null || points[i].y > maxPt.y) maxPt = points[i];
                    if(minPt === null || points[i].y < minPt.y) minPt = points[i];
                }
            }
            if (!maxPt || !minPt) return null;
            
            return {
                maxX: Math.round(maxPt.plotX + chart.plotLeft),
                maxY: Math.round(maxPt.plotY + chart.plotTop),
                minX: Math.round(minPt.plotX + chart.plotLeft),
                minY: Math.round(minPt.plotY + chart.plotTop)
            };
            """
            coords = driver.execute_script(js_get_pixels)

            if coords:
                action = ActionChains(driver)
                safe_name = station.replace(' ', '_').replace('/', '_')

                # ΤΟ ΑΝΘΡΩΠΙΝΟ ΧΕΡΙ: Πάει φυσικά το ποντίκι στο MAX
                action.move_to_element_with_offset(chart_container, coords['maxX'], coords['maxY']).perform()
                time.sleep(1.5) # Αναμονή να εμφανιστεί το συννεφάκι
                driver.save_screenshot(f"screenshots/{today}/{safe_name}_MAX.png")

                # ΤΟ ΑΝΘΡΩΠΙΝΟ ΧΕΡΙ: Πάει φυσικά το ποντίκι στο MIN
                action.move_to_element_with_offset(chart_container, coords['minX'], coords['minY']).perform()
                time.sleep(1.5)
                driver.save_screenshot(f"screenshots/{today}/{safe_name}_MIN.png")
                
                print(f"[{station}] Επιτυχία! Το ποντίκι βρήκε τα σημεία.")
            else:
                print(f"[{station}] Σφάλμα: Η καμπύλη δεν έχει δεδομένα.")

        except Exception as e:
            print(f"[{station}] Αποτυχία στο hover: {e}")
        
        # Ανανέωση σελίδας για να έχουμε καθαρή μνήμη για τον επόμενο σταθμό
        driver.refresh()
        time.sleep(8)
        driver.execute_script("""
            document.querySelectorAll('*').forEach(el => {
                var s = window.getComputedStyle(el);
                if(s.position === 'fixed' || s.position === 'sticky' || el.id.includes('cookie')) el.remove();
            });
        """)

except Exception as general_e:
    print(f"Γενικό Σφάλμα: {general_e}")
finally:
    driver.quit()
    print("Η σάρωση ολοκληρώθηκε.")
