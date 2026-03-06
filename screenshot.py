from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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
    print("ΕΚΚΙΝΗΣΗ: Μηχανική Σάρωση Όλων των Σταθμών (Native Mouse)...")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(15) # Περιμένουμε να φορτώσει πλήρως ο χάρτης

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(f"screenshots/{today}", exist_ok=True)

    # 1. ΦΩΤΟΓΡΑΦΙΑ ΑΣΦΑΛΕΙΑΣ (Για να μην είναι ποτέ άδειος ο φάκελος)
    driver.save_screenshot(f"screenshots/{today}/00_PROOF_OF_LIFE.png")
    print("Βγήκε η αρχική φωτογραφία! Ο φάκελος δημιουργήθηκε.")

    # 2. Καθαρισμός Cookies
    driver.execute_script("""
        document.querySelectorAll('*').forEach(el => {
            var s = window.getComputedStyle(el);
            if(s.position === 'fixed' || s.position === 'sticky' || el.id.includes('cookie')) el.remove();
        });
    """)
    time.sleep(2)

    # 3. Μετράμε πόσες πινέζες έχει ο χάρτης
    num_pins = driver.execute_script("return document.querySelectorAll('.leaflet-marker-icon').length;")
    print(f"ΒΡΕΘΗΚΑΝ ΣΥΝΟΛΙΚΑ {num_pins} ΠΙΝΕΖΕΣ! Ξεκινάω τη σάρωση...")

    if num_pins == 0:
        print("ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Δεν βρέθηκαν πινέζες. Κάτι μπλοκάρει τον χάρτη.")

    # 4. ΣΑΡΩΣΗ ΜΙΑ-ΜΙΑ ΤΙΣ ΠΙΝΕΖΕΣ (Σαν άνθρωπος)
    for i in range(num_pins):
        station_name = f"Station_{i}"
        try:
            # Επιστροφή στην κορυφή για να πατήσουμε την πινέζα
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Κλικ στην πινέζα
            driver.execute_script(f"document.querySelectorAll('.leaflet-marker-icon')[{i}].click();")
            time.sleep(2.5) # Αναμονή να ανοίξει το popup και να φορτώσουν τα δεδομένα

            # Ανάγνωση του ονόματος του σταθμού
            js_name = "var p = document.querySelector('.leaflet-popup-content, .card'); return p ? p.innerText.split('\\n')[0].trim() : 'Unknown';"
            station_name = driver.execute_script(js_name).replace('/', '_').replace(' ', '_')
            print(f"\n[{i+1}/{num_pins}] Επεξεργασία: {station_name}")

            # Σκρολ κάτω στο Διάγραμμα
            driver.execute_script("window.scrollBy(0, 850);")
            time.sleep(4) # Αναμονή να σχεδιαστεί η καμπύλη

            # 5. ΤΟ ΑΝΘΡΩΠΙΝΟ ΧΕΡΙ (Native JS Mouse Event)
            js_hover = """
            var isMax = arguments[0];
            var chart = Highcharts.charts.find(c => c && c.series && c.series[0].points);
            if (!chart) return false;
            
            var points = chart.series[0].points;
            var target = null;
            for(var j=0; j<points.length; j++) {
                if(points[j].y !== null) {
                    if(target === null) target = points[j];
                    else if(isMax && points[j].y > target.y) target = points[j];
                    else if(!isMax && points[j].y < target.y) target = points[j];
                }
            }
            if(!target) return false;

            // Δημιουργούμε ένα ΑΛΗΘΙΝΟ ψηφιακό κλικ/κίνηση ποντικιού
            var rect = chart.container.getBoundingClientRect();
            var clientX = rect.left + chart.plotLeft + target.plotX;
            var clientY = rect.top + chart.plotTop + target.plotY;
            var evt = new MouseEvent('mousemove', {
                clientX: clientX, clientY: clientY, bubbles: true, cancelable: true, view: window
            });
            chart.container.dispatchEvent(evt);
            
            // Back-up εντολή API για σιγουριά
            try {
                chart.tooltip.refresh(target);
                target.setState('hover');
                chart.xAxis[0].drawCrosshair(null, target);
            } catch(e) {}
            
            return true;
            """

            # Φωτογραφία MAX
            success_max = driver.execute_script(js_hover, True)
            time.sleep(1.5)
            if success_max:
                driver.save_screenshot(f"screenshots/{today}/{station_name}_MAX.png")
            else:
                driver.save_screenshot(f"screenshots/{today}/ERROR_{station_name}_MAX.png")

            # Φωτογραφία MIN
            success_min = driver.execute_script(js_hover, False)
            time.sleep(1.5)
            if success_min:
                driver.save_screenshot(f"screenshots/{today}/{station_name}_MIN.png")
            else:
                driver.save_screenshot(f"screenshots/{today}/ERROR_{station_name}_MIN.png")

            print(f"[{station_name}] Επιτυχία!")

        except Exception as e:
            print(f"[{station_name}] Σφάλμα: {e}")
            driver.save_screenshot(f"screenshots/{today}/CRASH_{station_name}.png")

        finally:
            # Επιστροφή πάνω και κλείσιμο του popup για να καθαρίσει ο χάρτης
            driver.execute_script("window.scrollTo(0, 0);")
            driver.execute_script("var closeBtn = document.querySelector('.leaflet-popup-close-button'); if(closeBtn) closeBtn.click();")
            time.sleep(1)

except Exception as general_e:
    print(f"Γενικό Σφάλμα Συστήματος: {general_e}")
finally:
    driver.quit()
    print("Η διαδικασία ολοκληρώθηκε.")
