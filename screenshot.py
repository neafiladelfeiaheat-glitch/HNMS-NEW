from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
import sys
from datetime import datetime

# Λήψη ορισμάτων από το Matrix
if len(sys.argv) < 3:
    sys.exit(1)

station_id = sys.argv[1]
station_name = sys.argv[2]

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,2000') 

# SSL Bypass (Η ασπίδα μας)
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.accept_insecure_certs = True
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)

try:
    print(f"[{station_name}] Εκκίνηση...")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(15) # Χρόνος για να φορτώσει η JS του χάρτη

    today = datetime.now().strftime("%Y-%m-%d")
    save_path = f"screenshots/{today}"
    os.makedirs(save_path, exist_ok=True)

    # 1. ΤΟ «ΑΝΘΡΩΠΙΝΟ ΧΕΡΙ» ΜΕΣΩ ΚΩΔΙΚΑ
    # Καλούμε απευθείας τη συνάρτηση που ανοίγει τον σταθμό, χωρίς να ψάχνουμε μενού
    select_script = f"if(typeof selectStation === 'function') {{ selectStation({station_id}); }} else {{ throw new Error('JS Not Ready'); }}"
    driver.execute_script(select_script)
    print(f"[{station_name}] Ο σταθμός επιλέχθηκε.")
    time.sleep(10) # Περιμένουμε να φορτώσουν τα δεδομένα του σταθμού και το διάγραμμα

    # 2. ΦΥΣΙΚΟ HOVER ΜΕ ActionChains
    # Υπολογίζουμε τα pixels της καμπύλης
    js_get_coords = """
    var chart = Highcharts.charts.find(c => c && c.series && c.series[0].points);
    if (!chart) return null;
    var points = chart.series[0].points.filter(p => p.y !== null);
    if (points.length === 0) return null;
    
    var maxP = points.reduce((a, b) => (a.y > b.y ? a : b));
    var minP = points.reduce((a, b) => (a.y < b.y ? a : b));
    
    return {
        maxX: maxP.plotX + chart.plotLeft,
        maxY: maxP.plotY + chart.plotTop,
        minX: minP.plotX + chart.plotLeft,
        minY: minP.plotY + chart.plotTop
    };
    """
    coords = driver.execute_script(js_get_coords)

    if coords:
        chart_container = driver.find_element(By.CSS_SELECTOR, ".highcharts-container")
        actions = ActionChains(driver)

        # MAX
        actions.move_to_element_with_offset(chart_container, coords['maxX'], coords['maxY']).perform()
        time.sleep(1.5)
        driver.save_screenshot(f"{save_path}/{station_name}_MAX.png")

        # MIN
        actions.move_to_element_with_offset(chart_container, coords['minX'], coords['minY']).perform()
        time.sleep(1.5)
        driver.save_screenshot(f"{save_path}/{station_name}_MIN.png")
        print(f"[{station_name}] Screenshots αποθηκεύτηκαν.")
    else:
        print(f"[{station_name}] Δεν βρέθηκαν δεδομένα στο διάγραμμα.")
        driver.save_screenshot(f"{save_path}/NO_DATA_{station_name}.png")

except Exception as e:
    print(f"[{station_name}] Σφάλμα: {e}")
finally:
    driver.quit()
