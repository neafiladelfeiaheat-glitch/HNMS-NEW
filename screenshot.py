import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080')
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)
target_stations = ["ΚΑΣΟΣ", "ΣΠΑΡΤΗ"]

try:
    print("Εκκίνηση Συστήματος Μαύρου Κουτιού...")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(12)

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(f"screenshots/{today}", exist_ok=True)

    # Σκοτώνουμε τα cookies
    driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.textContent.includes('Αποδοχή')) b.click(); });")
    time.sleep(2)

    # ΦΩΤΟΓΡΑΦΙΑ 1: ΕΓΓΥΗΣΗ ΟΤΙ Ο ΦΑΚΕΛΟΣ ΔΕΝ ΕΙΝΑΙ ΑΔΕΙΟΣ
    driver.save_screenshot(f"screenshots/{today}/1_INITIAL_VIEW.png")
    print("Βγήκε η αρχική φωτογραφία.")

    for station in target_stations:
        try:
            # ΒΗΜΑ 1: Πατάμε τον μεγεθυντικό φακό (Search icon)
            driver.execute_script("""
            document.querySelectorAll('i, svg, img, div, span').forEach(el => {
                let c = el.className || '';
                if (typeof c === 'string' && (c.includes('search') || c.includes('Search'))) {
                    el.click();
                }
            });
            """)
            time.sleep(2)
            driver.save_screenshot(f"screenshots/{today}/2_AFTER_SEARCH_CLICK_{station}.png")

            # ΒΗΜΑ 2: Βρίσκουμε το input και γράφουμε
            driver.execute_script(f"""
            var input = document.querySelector('input[type="text"]') || document.querySelector('input');
            if(input) {{
                input.value = '{station}';
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
            """)
            time.sleep(3)
            driver.save_screenshot(f"screenshots/{today}/3_AFTER_TYPING_{station}.png")

            # ΒΗΜΑ 3: Επιλέγουμε το αποτέλεσμα από τη λίστα
            driver.execute_script(f"""
            document.querySelectorAll('li, div, span, a').forEach(el => {{
                if(el.textContent.trim() === '{station}' && el.children.length === 0) {{
                    el.click();
                }}
            }});
            """)
            time.sleep(7)
            driver.save_screenshot(f"screenshots/{today}/4_AFTER_STATION_CLICK_{station}.png")

            # ΒΗΜΑ 4: Highcharts - "Ακούμπημα" και Λήψη
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
                print(f"ΕΠΙΤΥΧΙΑ ΓΙΑ: {station}")
            else:
                driver.save_screenshot(f"screenshots/{today}/5_HIGHCHARTS_ERROR_{station}.png")

        except Exception as e:
            driver.save_screenshot(f"screenshots/{today}/CRASH_{station}.png")
        
        # Ανανέωση σελίδας για να καθαρίσει το τοπίο για τον επόμενο
        driver.refresh()
        time.sleep(8)
        driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.textContent.includes('Αποδοχή')) b.click(); });")

finally:
    driver.quit()
