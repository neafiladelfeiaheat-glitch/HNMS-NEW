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

# SSL Bypass
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.accept_insecure_certs = True

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)
target_stations = ["ΕΛΛΗΝΙΚΟ", "ΚΑΣΟΣ", "ΣΠΑΡΤΗ"]

try:
    print("Εκκίνηση... Εφαρμογή γεωμετρικής ανάλυσης και φυσικών κλικ.")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(15) # Περιμένουμε τον χάρτη

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(f"screenshots/{today}", exist_ok=True)

    # Σκοτώνουμε τα ενοχλητικά cookies
    driver.execute_script("""
        document.querySelectorAll('*').forEach(el => {
            var s = window.getComputedStyle(el);
            if(s.position === 'fixed' || s.position === 'sticky' || el.id.includes('cookie')) el.remove();
        });
    """)
    time.sleep(2)

    for station in target_stations:
        print(f"\n--- Επεξεργασία: {station} ---")
        
        # 1. ΒΡΙΣΚΟΥΜΕ ΤΗΝ ΠΙΝΕΖΑ (Αν δεν είναι το Ελληνικό που ανοίγει αυτόματα)
        if station != "ΕΛΛΗΝΙΚΟ":
            print(f"Ψάχνω την πινέζα για {station} με φυσικά κλικ...")
            pins_count = driver.execute_script("return document.querySelectorAll('.leaflet-marker-icon').length;")
            found = False
            
            for i in range(pins_count):
                try:
                    # Κλικ στην πινέζα
                    driver.execute_script(f"document.querySelectorAll('.leaflet-marker-icon')[{i}].click();")
                    time.sleep(1) # Χρόνος να ανοίξει το popup
                    
                    # Διαβάζουμε το κείμενο
                    popup_text = driver.execute_script("var p = document.querySelector('.leaflet-popup-content, .info, .card'); return p ? p.textContent.toUpperCase() : '';")
                    
                    if station in popup_text:
                        found = True
                        print(f"ΒΡΕΘΗΚΕ Η ΠΙΝΕΖΑ ΓΙΑ: {station}!")
                        break
                        
                    # Κλείνουμε το λάθος popup για να μην μπλοκάρει την επόμενη πινέζα!
                    driver.execute_script("var cls = document.querySelector('.leaflet-popup-close-button'); if(cls) cls.click();")
                    time.sleep(0.5)
                except:
                    continue
            
            if not found:
                print(f"Αποτυχία: Δεν βρέθηκε πινέζα για {station}.")
                driver.save_screenshot(f"screenshots/{today}/ERROR_PIN_{station}.png")
                continue

        # 2. ΣΚΡΟΛ ΣΤΟ ΔΙΑΓΡΑΜΜΑ
        print("Σκρολάρω στο διάγραμμα...")
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(6) # Περιμένουμε να σχεδιαστεί η καμπύλη
        
        # 3. ΓΕΩΜΕΤΡΙΚΗ ΑΝΑΛΥΣΗ ΤΗΣ ΚΑΜΠΥΛΗΣ (Bypass προστασίας Highcharts)
        js_find_points = """
        var path = document.querySelector('.highcharts-graph');
        if (!path) return null;
        var d = path.getAttribute('d');
        var points = [];
        var parts = d.split(' ');
        var i = 0;
        while (i < parts.length) {
            if (parts[i] === 'M' || parts[i] === 'L') {
                var x = parseFloat(parts[i+1]);
                var y = parseFloat(parts[i+2]);
                if (!isNaN(x) && !isNaN(y)) points.push({x: x, y: y});
                i += 3;
            } else { i++; }
        }
        if (points.length === 0) return null;
        
        var maxT = points[0]; // Min Y = Max Temp
        var minT = points[0]; // Max Y = Min Temp
        for (var j = 1; j < points.length; j++) {
            if (points[j].y < maxT.y) maxT = points[j];
            if (points[j].y > minT.y) minT = points[j];
        }
        return {maxX: maxT.x, maxY: maxT.y, minX: minT.x, minY: minT.y};
        """
        
        indices = driver.execute_script(js_find_points)

        if indices:
            print("Τα γεωμετρικά σημεία βρέθηκαν. Κουνάω το ποντίκι...")
            action = ActionChains(driver)
            svg_element = driver.find_element(By.CSS_SELECTOR, '.highcharts-root')
            
            # Φυσική κίνηση ποντικιού στο Max
            action.move_to_element_with_offset(svg_element, int(indices['maxX']), int(indices['maxY'])).perform()
            time.sleep(1.5)
            driver.save_screenshot(f"screenshots/{today}/{station}_MAX.png")

            # Φυσική κίνηση ποντικιού στο Min
            action.move_to_element_with_offset(svg_element, int(indices['minX']), int(indices['minY'])).perform()
            time.sleep(1.5)
            driver.save_screenshot(f"screenshots/{today}/{station}_MIN.png")
            print(f"ΕΠΙΤΥΧΙΑ: {station} αποθηκεύτηκε!")
        else:
            print(f"Σφάλμα: Δεν βρέθηκε η γραμμή του διαγράμματος για {station}")
            driver.save_screenshot(f"screenshots/{today}/ERROR_CHART_{station}.png")
        
        # 4. Refresh για να ξεκινήσουμε "καθαροί" τον επόμενο σταθμό
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
