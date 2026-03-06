from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
from datetime import datetime

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
# Φτιάχνουμε την οθόνη "γίγαντα" (3000px ύψος) για να βλέπει και τον χάρτη πάνω και το γράφημα κάτω με τη μία!
chrome_options.add_argument('--window-size=1920,3000') 
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)
target_stations = ["ΚΑΣΟΣ", "ΣΠΑΡΤΗ"]

try:
    print("Εκκίνηση Λειτουργίας 'ΠΙΝΕΖΕΣ'...")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(12) 

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(f"screenshots/{today}", exist_ok=True)

    # 1. Η ΔΙΚΛΕΙΔΑ ΑΣΦΑΛΕΙΑΣ: Βγάζουμε ΠΑΝΤΑ την αρχική φωτογραφία του χάρτη!
    driver.save_screenshot(f"screenshots/{today}/0_MAP_START.png")
    print("Η αρχική φωτογραφία του χάρτη αποθηκεύτηκε. Ο φάκελος δεν θα είναι άδειος.")

    # Σκοτώνουμε τα cookies
    driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.textContent.includes('Αποδοχή')) b.click(); });")
    time.sleep(2)

    for station in target_stations:
        print(f"--- Ξεκινάω να πατάω πινέζες για: {station} ---")
        
        # 2. Το ρομπότ πατάει τις πινέζες ΜΙΑ-ΜΙΑ μέχρι να δει το όνομα που ψάχνουμε
        js_find_pin = f"""
        var cb = arguments[arguments.length - 1]; 
        (async function() {{
            var pins = document.querySelectorAll('.leaflet-marker-icon, img[src*="marker"], [class*="marker"]');
            if (pins.length === 0) {{ cb("NO_PINS"); return; }}
            
            for(var i=0; i<pins.length; i++) {{
                try {{ pins[i].click(); }} catch(e) {{}}
                await new Promise(r => setTimeout(r, 1000)); // Περιμένουμε 1 δευτερόλεπτο να ανοίξει το παραθυράκι
                
                // Ελέγχουμε αν το όνομα (π.χ. ΚΑΣΟΣ) εμφανίστηκε στο popup
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
        
        # Δίνουμε 2 λεπτά χρόνο στο ρομπότ να ψάξει όλες τις πινέζες
        driver.set_script_timeout(120) 
        result = driver.execute_async_script(js_find_pin)
        
        if result != "FOUND":
            print(f"Αποτυχία: Πάτησα όλες τις πινέζες αλλά δεν βρήκα το '{station}'.")
            driver.save_screenshot(f"screenshots/{today}/ERROR_{station}_NOT_FOUND.png")
            continue
            
        print(f"ΒΡΗΚΑ ΤΗΝ ΠΙΝΕΖΑ ΓΙΑ {station}! Σκρολάρω προς τα κάτω για το γράφημα...")
        
        # 3. Σκρολάρουμε προς τα κάτω για το διάγραμμα
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(6) # Περιμένουμε να σχεδιαστεί η καμπύλη Highcharts
        
        # Φωτογραφία ελέγχου ότι κατέβηκε σωστά
        driver.save_screenshot(f"screenshots/{today}/1_SCROLLED_{station}.png")
        
        # 4. Βρίσκουμε το Max/Min και κάνουμε Hover
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
            print(f"Το διάγραμμα δεν φορτώθηκε για {station}.")
            driver.save_screenshot(f"screenshots/{today}/ERROR_{station}_NO_CHART.png")
            
        # 5. Ανανέωση σελίδας για να κλείσει η πινέζα και να πάμε στον επόμενο σταθμό
        driver.refresh()
        time.sleep(8)
        try: driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.textContent.includes('Αποδοχή')) b.click(); });")
        except: pass

finally:
    driver.quit()
