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

# --- SSL BYPASS (Που μας έσωσε) ---
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.accept_insecure_certs = True

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)

# Προσθέσαμε το Ελληνικό όπως ζήτησες
target_stations = ["ΕΛΛΗΝΙΚΟ", "ΚΑΣΟΣ", "ΣΠΑΡΤΗ"]

try:
    print("Εκκίνηση... Περάσαμε το SSL!")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(15) # Περιμένουμε να φορτώσει ο χάρτης

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(f"screenshots/{today}", exist_ok=True)

    # 1. ΕΞΑΥΛΩΣΗ COOKIES & OVERLAYS (Απόλυτη διαγραφή για να μην κρύβουν πινέζες)
    driver.execute_script("""
        document.querySelectorAll('*').forEach(el => {
            var style = window.getComputedStyle(el);
            if(style.position === 'fixed' || style.position === 'sticky' || el.id.includes('cookie')) {
                el.remove();
            }
        });
    """)
    print("Τα cookies εξαϋλώθηκαν.")
    time.sleep(2)

    for station in target_stations:
        print(f"\n--- Επεξεργασία: {station} ---")
        
        # Αν ΔΕΝ είναι το Ελληνικό, πρέπει να βρούμε την πινέζα του
        if station != "ΕΛΛΗΝΙΚΟ":
            print(f"Ψάχνω την πινέζα για {station}...")
            js_find_pin = f"""
            var cb = arguments[arguments.length - 1]; 
            (async function() {{
                var pins = document.querySelectorAll('.leaflet-marker-icon, img[src*="marker"]');
                if (pins.length === 0) {{ cb("NO_PINS"); return; }}
                
                for(var i=0; i<pins.length; i++) {{
                    try {{ pins[i].click(); }} catch(e) {{}}
                    await new Promise(r => setTimeout(r, 1200)); 
                    
                    var popups = document.querySelectorAll('.leaflet-popup-content, .info, .card');
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
            # Δίνουμε 2.5 λεπτά στο ρομπότ να πατήσει όλες τις πινέζες μέχρι να το βρει
            driver.set_script_timeout(150)
            result = driver.execute_async_script(js_find_pin)
            
            if result != "FOUND":
                print(f"Αποτυχία: Δεν βρέθηκε η πινέζα για {station}.")
                driver.save_screenshot(f"screenshots/{today}/ERROR_PIN_{station}.png")
                continue
            else:
                print(f"Βρέθηκε η πινέζα για {station}! Σκρολάρω...")

        # 2. ΣΚΡΟΛ ΚΑΤΩ ΣΤΟ ΔΙΑΓΡΑΜΜΑ (Ισχύει και για το Ελληνικό και για τις πινέζες)
        driver.execute_script("window.scrollBy(0, 900);")
        time.sleep(6) # Χρόνος για να σχεδιαστεί η καμπύλη Highcharts
        
        # 3. HOVER ΓΙΑ MAX ΚΑΙ MIN
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
            print(f"ΕΠΙΤΥΧΙΑ: Αποθηκεύτηκαν τα διαγράμματα για {station}")
        else:
            print(f"Σφάλμα: Το διάγραμμα δεν φορτώθηκε για {station}")
            driver.save_screenshot(f"screenshots/{today}/ERROR_CHART_{station}.png")
        
        # 4. ΑΝΑΝΕΩΣΗ ΣΕΛΙΔΑΣ (Για να καθαρίσει ο χάρτης για την επόμενη πινέζα)
        driver.refresh()
        time.sleep(10)
        # Σκοτώνουμε ξανά τα cookies που ξαναβγαίνουν μετά το refresh
        driver.execute_script("""
            document.querySelectorAll('*').forEach(el => {
                var style = window.getComputedStyle(el);
                if(style.position === 'fixed' || style.position === 'sticky' || el.id.includes('cookie')) el.remove();
            });
        """)

finally:
    driver.quit()
    print("Διαδικασία ολοκληρώθηκε.")
