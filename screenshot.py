from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os
from datetime import datetime

# Ρυθμίσεις για να τρέχει στο GitHub Actions
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080')
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)

# Η ΛΙΣΤΑ ΣΟΥ: Αττική + Κάσος, Κάρπαθος, Ρόδος, Σπάρτη
target_stations = [
    "Ελληνικό", "Ελ. Βενιζέλος 03L", "Ελ. Βενιζέλος 21L", "Ελευσίνα", 
    "Μαλακάσα", "Μαρκόπουλο", "Μέγαρα", "Oaka", "Πάρνηθα", "Τατόι", "Βούλα",
    "Κάσος", "Κάρπαθος", "Ρόδος", "Σπάρτη"
]

def run_automation():
    try:
        driver.get("https://www.emy.gr/hnms-stations")
        time.sleep(10) # Αναμονή για να φορτώσει το portal

        # Δημιουργία φακέλου με τη σημερινή ημερομηνία
        today = datetime.now().strftime("%Y-%m-%d")
        base_path = f"screenshots/{today}"
        os.makedirs(base_path, exist_ok=True)

        for station in target_stations:
            print(f"Επεξεργασία σταθμού: {station}")
            try:
                # Κλικ στον σταθμό από τη λίστα
                station_btn = driver.find_element(By.XPATH, f"//div[contains(text(), '{station}')]")
                driver.execute_script("arguments[0].click();", station_btn)
                time.sleep(7) # Χρόνος για να σχεδιαστεί το Highcharts διάγραμμα

                # JavaScript για εύρεση Μέγιστης (Max) και Ελάχιστης (Min) και "Hover"
                js_logic = """
                var chart = Highcharts.charts[0];
                var data = chart.series[0].data;
                var maxP = data.reduce((max, p) => p.y > max.y ? p : max, data[0]);
                var minP = data.reduce((min, p) => p.y < min.y ? p : min, data[0]);
                return {maxIdx: maxP.index, minIdx: minP.index};
                """
                indices = driver.execute_script(js_logic)

                # 1. Screenshot για Μέγιστη Τιμή
                driver.execute_script(f"Highcharts.charts[0].tooltip.refresh(Highcharts.charts[0].series[0].data[{indices['maxIdx']}]);")
                time.sleep(1)
                driver.save_screenshot(f"{base_path}/{station}_MAX.png")

                # 2. Screenshot για Ελάχιστη Τιμή
                driver.execute_script(f"Highcharts.charts[0].tooltip.refresh(Highcharts.charts[0].series[0].data[{indices['minIdx']}]);")
                time.sleep(1)
                driver.save_screenshot(f"{base_path}/{station}_MIN.png")

            except Exception as e:
                print(f"Σφάλμα στον σταθμό {station}: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()
