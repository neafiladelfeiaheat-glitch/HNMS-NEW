from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
from datetime import datetime

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080')
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)

# Ξεκινάμε με 4 σταθμούς για την απόλυτη δοκιμή (Κάσος, Σπάρτη, Ρόδος, Μαρκόπουλο)
target_stations = ["ΚΑΣΟΣ", "ΣΠΑΡΤΗ", "ΡΟΔΟΣ", "ΜΑΡΚΟΠΟΥΛΟ"] 

try:
    print("Εκκίνηση...")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(8)

    # 1. Η ΕΞΑΫΛΩΣΗ ΤΗΣ ΑΣΠΙΔΑΣ (Cookies)
    # Βρίσκει οτιδήποτε εμποδίζει στην οθόνη (fixed elements) και το διαγράφει εντελώς
    driver.execute_script("""
        document.querySelectorAll('button').forEach(b => { if(b.textContent.includes('Αποδοχή')) b.click(); });
        document.querySelectorAll('*').forEach(el => {
            var style = window.getComputedStyle(el);
            if(style.position === 'fixed' || style.position === 'sticky') {
                el.remove();
            }
        });
    """)
    print("Τα εμπόδια διαγράφηκαν.")
    time.sleep(2)

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(f"screenshots/{today}", exist_ok=True)

    for station in target_stations:
        print(f"Αναζήτηση για: {station}")
        try:
            # 2. Προσομοίωση ανθρώπου: Κλικ στην αναζήτηση
            try:
                search_icon = driver.find_element(By.CSS_SELECTOR, ".fa-search, [class*='search']")
                driver.execute_script("arguments[0].click();", search_icon)
                time.sleep(1)
            except: pass

            # 3. Πληκτρολόγηση και ENTER (δεν ψάχνουμε τυφλά)
            search_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='text' or contains(@class, 'search') or contains(@placeholder, 'Search')]")))
            search_input.clear()
            search_input.send_keys(station)
            search_input.send_keys(Keys.ENTER)
            
            # 4. Αναμονή να φορτώσει το γράφημα Highcharts (Το "Ζουμί")
            time.sleep(7) 

            # 5. Υπολογισμός Max/Min & Φωτογράφιση
            js_indices = """
            var chart = Highcharts.charts[0];
            if (!chart) return null;
            var data = chart.series[0].data;
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
                print(f"Αποτυχία: Το γράφημα δεν άνοιξε για {station}")

            # Ανανέωση της σελίδας για να καθαρίσει το τοπίο για τον επόμενο σταθμό
            driver.refresh()
            time.sleep(6)
            driver.execute_script("""
                document.querySelectorAll('*').forEach(el => {
                    var style = window.getComputedStyle(el);
                    if(style.position === 'fixed' || style.position === 'sticky') el.remove();
                });
            """)

        except Exception as e:
            print(f"Σφάλμα στο {station}: {e}")
            driver.refresh()
            time.sleep(6)

finally:
    driver.quit()
