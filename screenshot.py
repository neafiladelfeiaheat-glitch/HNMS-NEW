from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
from datetime import datetime

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,3000') # Γιγάντια οθόνη

# SSL Bypass - Η ασπίδα μας 
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.accept_insecure_certs = True

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)
target_stations = ["ΕΛΛΗΝΙΚΟ", "ΚΑΣΟΣ", "ΣΠΑΡΤΗ"]

try:
    print("Εκκίνηση... Διόρθωση Πινεζών και Tooltip!")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(12) 

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(f"screenshots/{today}", exist_ok=True)

    # Σκοτώνουμε τα cookies
    driver.execute_script("""
        document.querySelectorAll('*').forEach(el => {
            var s = window.getComputedStyle(el);
            if(s.position === 'fixed' || s.position === 'sticky' || el.id.includes('cookie')) el.remove();
        });
    """)
    time.sleep(2)

    for station in target_stations:
        print(f"\n--- Επεξεργασία: {station} ---")
        
        # 1. ΒΡΙΣΚΟΥΜΕ ΤΗΝ ΠΙΝΕΖΑ (Με έξυπνο κλείσιμο)
        if station != "ΕΛΛΗΝΙΚΟ":
            print(f"Ψάχνω την πινέζα για {station}...")
            js_find_pin = f"""
            var cb = arguments[arguments.length - 1]; 
            var target = '{station}';
            var pins = document.querySelectorAll('.leaflet-marker-icon, img[src*="marker"]');
            if (pins.length === 0) {{ cb("NO_PINS"); return; }}
            
            (async function() {{
                for(var i=0; i<pins.length; i++) {{
                    try {{ pins[i].click(); }} catch(e) {{}}
                    await new Promise(r => setTimeout(r, 1000)); // Περιμένουμε το popup
                    
                    var popup = document.querySelector('.leaflet-popup-content, .card, .info');
                    if (popup && popup.textContent.toUpperCase().includes(target)) {{
                        cb("FOUND");
                        return;
                    }}
                    
                    // ΑΝ ΔΕΝ ΕΙΝΑΙ ΣΩΣΤΟ: Πατάμε το X για να κλείσει και να μην μπλοκάρει
                    var closeBtn = document.querySelector('.leaflet-popup-close-button');
                    if(closeBtn) {{ closeBtn.click(); }}
                    else {{
                        var mapBg = document.querySelector('.leaflet-container');
                        if(mapBg) {{ mapBg.click(); }}
                    }}
                    await new Promise(r => setTimeout(r, 500));
                }}
                cb("NOT_FOUND");
            }})();
            """
            driver.set_script_timeout(180) # Δίνουμε 3 λεπτά για να δοκιμάσει όλες τις πινέζες
            result = driver.execute_async_script(js_find_pin)
            
            if result != "FOUND":
                print(f"Αποτυχία: Δεν βρέθηκε η πινέζα για {station}.")
                driver.save_screenshot(f"screenshots/{today}/ERROR_PIN_{station}.png")
                continue
            else:
                print(f"Βρέθηκε η πινέζα για {station}! Σκρολάρω...")

        # 2. ΣΚΡΟΛ ΣΤΟ ΔΙΑΓΡΑΜΜΑ
        driver.execute_script("window.scrollBy(0, 850);")
        time.sleep(6) # Περιμένουμε να σχεδιαστεί 
        
        # 3. Ο ΜΟΝΑΔΙΚΟΣ ΣΩΣΤΟΣ ΤΡΟΠΟΣ ΓΙΑ ΤΟ HOVER ΣΤΟ HIGHCHARTS
        js_get_indices = """
        if(typeof Highcharts === 'undefined' || !Highcharts.charts || !Highcharts.charts[0]) return null;
        var points = Highcharts.charts[0].series[0].points; // Εδώ ήταν το λάθος μου! Πρέπει να είναι .points
        if(!points || points.length === 0) return null;
        
        var maxIdx = 0;
        var minIdx = 0;
        for(var i=1; i<points.length; i++) {
            if(points[i].y !== null && points[maxIdx].y !== null && points[i].y > points[maxIdx].y) maxIdx = i;
            if(points[i].y !== null && points[minIdx].y !== null && points[i].y < points[minIdx].y) minIdx = i;
        }
        return {max: maxIdx, min: minIdx};
        """
        indices = driver.execute_script(js_get_indices)

        if indices:
            # Τώρα ξυπνάει το tooltip με 100% επιτυχία
            driver.execute_script(f"Highcharts.charts[0].tooltip.refresh(Highcharts.charts[0].series[0].points[{indices['max']}]);")
            time.sleep(1)
            driver.save_screenshot(f"screenshots/{today}/{station}_MAX.png")

            driver.execute_script(f"Highcharts.charts[0].tooltip.refresh(Highcharts.charts[0].series[0].points[{indices['min']}]);")
            time.sleep(1)
            driver.save_screenshot(f"screenshots/{today}/{station}_MIN.png")
            print(f"ΕΠΙΤΥΧΙΑ: {station} (Τα διαγράμματα βγήκαν!)")
        else:
            print(f"Σφάλμα: Το διάγραμμα δεν φορτώθηκε για {station}")
            driver.save_screenshot(f"screenshots/{today}/ERROR_CHART_{station}.png")
        
        # 4. Ανανέωση σελίδας
        driver.refresh()
        time.sleep(10)
        driver.execute_script("""
            document.querySelectorAll('*').forEach(el => {
                var s = window.getComputedStyle(el);
                if(s.position === 'fixed' || s.position === 'sticky' || el.id.includes('cookie')) el.remove();
            });
        """)

finally:
    driver.quit()
    print("Διαδικασία ολοκληρώθηκε.")
