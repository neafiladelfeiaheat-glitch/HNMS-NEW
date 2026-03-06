from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os
from datetime import datetime

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
# Οθόνη "γίγαντας" (3000 pixels ύψος) για να χωράει ο χάρτης και το γράφημα από κάτω
chrome_options.add_argument('--window-size=1920,3000') 
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)

# Δοκιμή με Κάσο και Σπάρτη
target_stations = ["ΚΑΣΟΣ", "ΣΠΑΡΤΗ"]

try:
    print("Επαναπροσδιορισμός: Λειτουργία 'ΠΙΝΕΖΕΣ'")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(15) # Περιμένουμε να φορτώσει ο χάρτης και οι πινέζες

    # Σκοτώνουμε τα cookies
    driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.textContent.includes('Αποδοχή')) b.click(); });")
    time.sleep(2)

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(f"screenshots/{today}", exist_ok=True)

    for station in target_stations:
        print(f"--- Ψάχνω την πινέζα για: {station} ---")
        
        # Βρίσκουμε όλες τις πινέζες (τα εικονίδια) πάνω στον χάρτη
        pins = driver.find_elements(By.CSS_SELECTOR, 'img[src*="marker"], img[src*="pin"], .leaflet-marker-icon, [class*="marker"]')
        print(f"Βρέθηκαν συνολικά {len(pins)} πινέζες. Ξεκινάω να πατάω...")
        
        found = False
        for pin in pins:
            try:
                # 1. Πατάμε την πινέζα όπως ακριβώς κάνεις εσύ
                driver.execute_script("arguments[0].click();", pin)
                time.sleep(0.5) # Μικρή παύση να ανοίξει το παραθυράκι του σταθμού
                
                # 2. Διαβάζουμε αν το όνομα του σταθμού (π.χ. ΣΠΑΡΤΗ) εμφανίστηκε
                popups = driver.find_elements(By.CSS_SELECTOR, '[class*="popup"], [class*="info"], .card, .panel, .leaflet-popup-content')
                for p in popups:
                    if station in p.text.upper():
                        found = True
                        break
                        
                if found:
                    break
            except:
                continue
                
        if not found:
            print(f"Αποτυχία: Δεν βρέθηκε η πινέζα για {station}.")
            continue
            
        print(f"Βρέθηκε η πινέζα για {station}! Σκρολάρω προς τα κάτω για το διάγραμμα...")
        
        # 3. Σκρολάρουμε προς τα κάτω στοχευμένα στο γράφημα Highcharts
        driver.execute_script("""
            var chartDiv = document.querySelector('.highcharts-container, [id*="highcharts"]');
            if (chartDiv) {
                chartDiv.scrollIntoView({block: 'center', behavior: 'smooth'});
            } else {
                window.scrollTo(0, 1500); // Αν δεν το βρει, πάει απλά κάτω
            }
        """)
        time.sleep(8) # Αναμονή για να σχεδιαστεί η καμπύλη
        
        # 4. Βρίσκουμε Max/Min και κάνουμε Hover
        js_indices = """
        if(typeof Highcharts === 'undefined' || !Highcharts.charts[0]) return null;
        var chart = Highcharts.charts[0];
        var data = chart.series[0].data;
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
            print(f"Το διάγραμμα δεν φορτώθηκε κάτω για τον σταθμό {station}.")
            
        # 5. Ανανέωση σελίδας για να κλείσει η πινέζα και να πάμε στον επόμενο
        driver.refresh()
        time.sleep(10)
        try: driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.textContent.includes('Αποδοχή')) b.click(); });")
        except: pass

finally:
    driver.quit()
