from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
from datetime import datetime

# --- Ρυθμίσεις Browser ---
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080')
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)

# Η λίστα των σταθμών με τα ΕΣΩΤΕΡΙΚΑ IDs της ΕΜΥ (για να μην ψάχνουμε πινέζες)
target_stations = {
    "Ελληνικό": "72",
    "Ελευσίνα": "81",
    "Ελ. Βενιζέλος 03L": "28",
    "Μαλακάσα": "49",
    "Μαρκόπουλο": "48",
    "Μέγαρα": "51",
    "Oaka": "73",
    "Πάρνηθα": "63",
    "Τατόι": "55",
    "Βούλα": "303",
    "Κάσος": "41",
    "Κάρπαθος": "8",
    "Ρόδος": "59",
    "Σπάρτη": "53"
}

try:
    print("--- ΕΚΚΙΝΗΣΗ DIRECT ACCESS ---")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(10) # Περιμένουμε την αρχική φόρτωση

    # Βίαιο κλείσιμο των Cookies (που είδαμε στη φωτογραφία ότι εμποδίζουν)
    try:
        driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.textContent.includes('Αποδοχή')) b.click(); })")
        time.sleep(2)
    except:
        pass

    # Δημιουργία φακέλου
    today = datetime.now().strftime("%Y-%m-%d")
    save_path = f"screenshots/{today}"
    os.makedirs(save_path, exist_ok=True)

    # Πάμε σε κάθε σταθμό μέσω του ID του!
    for name, station_id in target_stations.items():
        print(f"Ανάλυση σταθμού: {name} (ID: {station_id})")
        try:
            # Το μαγικό JavaScript: Λέμε στο site "Επέλεξε αυτόν τον σταθμό"
            # Αυτό παρακάμπτει εντελώς τον χάρτη!
            js_select = f"""
            // Βρίσκουμε την κεντρική λειτουργία επιλογής σταθμού (αν υπάρχει στο scope)
            // Εναλλακτικά, προσομοιώνουμε το API call.
            var selectElement = document.querySelector('select.form-control'); // Αν υπάρχει κρυφό select
            if (selectElement) {{
                selectElement.value = '{station_id}';
                selectElement.dispatchEvent(new Event('change'));
                return true;
            }}
            
            // Αν όχι, ψάχνουμε τη λίστα που τροφοδοτεί το Search
            var items = document.querySelectorAll('li, div.item'); // Προσαρμογή
            for(var i=0; i<items.length; i++) {{
                 // Αν το στοιχείο έχει ένα attribute με το ID ή το όνομα
                 if (items[i].getAttribute('data-value') === '{station_id}' || items[i].textContent.includes('{name}')) {{
                     items[i].click();
                     return true;
                 }}
            }}
            return false;
            """
            
            success = driver.execute_script(js_select)
            
            if not success:
                print(f"Αποτυχία: Δεν μπόρεσα να φορτώσω τον σταθμό {name} με ID {station_id}.")
                continue

            # Αναμονή για το γράφημα Highcharts
            time.sleep(6)

            # Εύρεση Max/Min και Hover
            js_indices = """
            var chart = Highcharts.charts[0];
            if (!chart) return null;
            var data = chart.series[0].data;
            var maxP = data.reduce((max, p) => p.y > max.y ? p : max, data[0]);
            var minP = data.reduce((min, p) => p.y < min.y ? p : min, data[0]);
            return {maxIdx: maxP.index, minIdx: minP.index};
            """
            indices = driver.execute_script(js_indices)

            if not indices:
                 print(f"Το διάγραμμα για το {name} δεν φόρτωσε σωστά.")
                 continue

            # Τραβάμε τα Screenshots
            driver.execute_script(f"Highcharts.charts[0].tooltip.refresh(Highcharts.charts[0].series[0].data[{indices['maxIdx']}]);")
            time.sleep(1)
            driver.save_screenshot(f"{save_path}/{name.replace(' ', '_')}_MAX.png")
            print(f"-> {name} MAX OK")

            driver.execute_script(f"Highcharts.charts[0].tooltip.refresh(Highcharts.charts[0].series[0].data[{indices['minIdx']}]);")
            time.sleep(1)
            driver.save_screenshot(f"{save_path}/{name.replace(' ', '_')}_MIN.png")
            print(f"-> {name} MIN OK")

        except Exception as e:
            print(f"Σφάλμα κατά την επεξεργασία του {name}: {e}")
            
finally:
    driver.quit()
    print("Η διαδικασία ολοκληρώθηκε.")
