from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
from datetime import datetime

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,3000') # Οθόνη "γίγαντας"

# --- ΟΙ 3 ΜΑΓΙΚΕΣ ΓΡΑΜΜΕΣ ΓΙΑ ΝΑ ΠΕΡΑΣΟΥΜΕ ΤΟΝ ΚΟΚΚΙΝΟ ΤΟΙΧΟ ---
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.accept_insecure_certs = True
# -------------------------------------------------------------

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)
target_stations = ["ΚΑΣΟΣ", "ΣΠΑΡΤΗ"]

try:
    print("Εκκίνηση Λειτουργίας 'ΠΙΝΕΖΕΣ' με SSL Bypass...")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(12) 

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(f"screenshots/{today}", exist_ok=True)

    # Βγάζουμε την αρχική φωτογραφία για να δούμε ότι μπήκαμε!
    driver.save_screenshot(f"screenshots/{today}/0_MAP_START.png")
    print("Περάσαμε την ασπίδα! Ο χάρτης φόρτωσε.")

    # Σκοτώνουμε τα cookies
    driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.textContent.includes('Αποδοχή')) b.click(); });")
    time.sleep(2)

    for station in target_stations:
        print(f"--- Ψάχνω την πινέζα για: {station} ---")
        
        js_find_pin = f"""
        var cb = arguments[arguments.length - 1]; 
        (async function() {{
            var pins = document.querySelectorAll('.leaflet-marker-icon, img[src*="marker"], [class*="marker"]');
            if (pins.length === 0) {{ cb("NO_PINS"); return; }}
            
            for(var i=0; i<pins.length; i++) {{
                try {{ pins[i].click(); }} catch(e) {{}}
                await new Promise(r => setTimeout(r, 1000)); 
                
                var popups = document.querySelectorAll('.leaflet-popup-content, [class*="popup"], .card, .info');
                for(var j=0; j<popups.length; j++) {{
                    if(popups[j].textContent.toUpperCase().includes('{station}')) {{
                        cb("FOUND");
                        return;
                    }}
                }}
            }}
            cb("NOT_FOUND");
        }})();
        """
        
        driver.set_script_timeout(120) 
        result = driver.execute_async_script(js_find_pin)
        
        if result != "FOUND":
            print(f"Αποτυχία: Δεν βρήκα την πινέζα για '{station}'.")
            continue
            
        print(f"ΒΡΗΚΑ ΤΗΝ ΠΙΝΕΖΑ ΓΙΑ {station}! Σκρολάρω...")
        
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(6) 
        
        js_indices = """
        if(typeof Highcharts === 'undefined' || !Highcharts.charts[0]) return null;
        var data = Highcharts.charts[0].series[0].data;
        if(!data || data.length === 0) return null;
        var maxP = data.reduce((max, p) => p.y > max.y ? p : max, data[0]);
        var minP = data.reduce((min, p) => p.y < min.y ? p : min, data[0]);
        return {maxIdx: maxP.index, minIdx: minP.index};
        """
        indices = driver.execute_script(js_indices)

        if indices:
            driver.execute_script(f"Highcharts.charts[0].tooltip.refresh(Highcharts.charts[0].series[0].data[{indices['maxIdx']}]);")
            time.sleep(1)
            driver.save_screenshot(f"screenshots/{today}/{station}_MAX.png")

            driver.execute_script(f"Highcharts.charts[0].tooltip.refresh(Highcharts.charts[0].series[0].data[{indices['minIdx']}]);")
            time.sleep(1)
            driver.save_screenshot(f"screenshots/{today}/{station}_MIN.png")
            print(f"ΕΠΙΤΥΧΙΑ: {station}")
        else:
            print(f"Το διάγραμμα δεν φορτώθηκε για {station}.")
            
        driver.refresh()
        time.sleep(8)
        try: driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.textContent.includes('Αποδοχή')) b.click(); });")
        except: pass

finally:
    driver.quit()
