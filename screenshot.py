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
chrome_options.add_argument('--window-size=1920,3000')

# Η Ασπίδα SSL 
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.accept_insecure_certs = True

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)
target_stations = ["ΕΛΛΗΝΙΚΟ", "ΚΑΣΟΣ", "ΣΠΑΡΤΗ"]

try:
    print("--- ZERO BASE ΕΚΚΙΝΗΣΗ ---")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(15) 

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(f"screenshots/{today}", exist_ok=True)

    # Καθαρισμός ενοχλητικών στοιχείων
    driver.execute_script("""
        document.querySelectorAll('*').forEach(el => {
            var s = window.getComputedStyle(el);
            if(s.position === 'fixed' || s.position === 'sticky' || el.id.includes('cookie')) el.remove();
        });
    """)
    time.sleep(2)

    for station in target_stations:
        print(f"\n[{station}] Ξεκινάει η διαδικασία...")
        
        try:
            # 1. ΜΗΔΕΝΙΚΗ ΒΑΣΗ ΓΙΑ ΤΙΣ ΠΙΝΕΖΕΣ (Σταθερός έλεγχος 1 προς 1)
            if station != "ΕΛΛΗΝΙΚΟ":
                pins = driver.find_elements(By.CSS_SELECTOR, '.leaflet-marker-icon, img[src*="marker"]')
                print(f"[{station}] Βρέθηκαν {len(pins)} πινέζες. Ψάχνω μία-μία...")
                found = False
                
                for idx, pin in enumerate(pins):
                    try:
                        driver.execute_script("arguments[0].click();", pin)
                        time.sleep(1.2) # Δίνουμε χρόνο να ανοίξει σίγουρα το popup
                        
                        popups = driver.find_elements(By.CSS_SELECTOR, '.leaflet-popup-content, .card, .info')
                        if popups:
                            text = popups[0].text.upper()
                            if station in text:
                                found = True
                                print(f"[{station}] ΒΡΕΘΗΚΕ! (Πινέζα {idx+1})")
                                break
                            
                            # ΑΝ ΔΕΝ ΕΙΝΑΙ ΣΩΣΤΗ: Κλείνουμε ΥΠΟΧΡΕΩΤΙΚΑ το popup
                            close_btns = driver.find_elements(By.CSS_SELECTOR, '.leaflet-popup-close-button')
                            if close_btns:
                                driver.execute_script("arguments[0].click();", close_btns[0])
                                time.sleep(0.5)
                    except Exception as e:
                        continue
                
                if not found:
                    print(f"[{station}] ΑΠΟΤΥΧΙΑ: Δεν βρέθηκε πουθενά.")
                    driver.save_screenshot(f"screenshots/{today}/ERROR_PIN_{station}.png")
                    continue

            # 2. ΣΚΡΟΛ ΣΤΟ ΔΙΑΓΡΑΜΜΑ
            driver.execute_script("window.scrollBy(0, 850);")
            time.sleep(6) 
            
            # 3. ΜΗΔΕΝΙΚΗ ΒΑΣΗ ΓΙΑ HIGHCHARTS (Βίαιη ενεργοποίηση Tooltip & Crosshair)
            js_highcharts = """
            try {
                var chart = Highcharts.charts.find(c => c && c.series);
                if(!chart) return false;
                var series = chart.series.find(s => s.visible && s.data.length > 0 && s.points);
                if(!series) return false;
                
                var points = series.points;
                var target = points[0];
                for(var i=1; i<points.length; i++) {
                    if(points[i].y !== null && points[i].y ARG target.y) {
                        target = points[i];
                    }
                }
                
                // Το απόλυτο bypass: Ξυπνάμε tooltip, crosshair και hover state ταυτόχρονα
                chart.tooltip.refresh(target);
                if(chart.xAxis[0]) chart.xAxis[0].drawCrosshair(null, target);
                target.setState('hover');
                return true;
            } catch(e) { return false; }
            """
            
            # MAX
            success_max = driver.execute_script(js_highcharts.replace("ARG", ">"))
            if success_max:
                time.sleep(1.5)
                driver.save_screenshot(f"screenshots/{today}/{station}_MAX.png")
            else:
                driver.save_screenshot(f"screenshots/{today}/ERROR_CHART_{station}_MAX.png")

            # MIN
            success_min = driver.execute_script(js_highcharts.replace("ARG", "<"))
            if success_min:
                time.sleep(1.5)
                driver.save_screenshot(f"screenshots/{today}/{station}_MIN.png")
            else:
                driver.save_screenshot(f"screenshots/{today}/ERROR_CHART_{station}_MIN.png")

            print(f"[{station}] ΟΛΟΚΛΗΡΩΘΗΚΕ!")

            # Ανανέωση σελίδας για να έχουμε καθαρό χάρτη για τον επόμενο
            driver.refresh()
            time.sleep(10)
            driver.execute_script("""
                document.querySelectorAll('*').forEach(el => {
                    var s = window.getComputedStyle(el);
                    if(s.position === 'fixed' || s.position === 'sticky' || el.id.includes('cookie')) el.remove();
                });
            """)

        except Exception as e:
            print(f"[{station}] ΣΦΑΛΜΑ: {e}")
            driver.save_screenshot(f"screenshots/{today}/CRASH_{station}.png")
            driver.refresh()
            time.sleep(10)
            continue 

finally:
    driver.quit()
    print("ΤΕΛΟΣ ZERO BASE.")
