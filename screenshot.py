from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
from datetime import datetime

# --- ΡΥΘΜΙΣΕΙΣ "ΒΑΡΕΩΣ ΤΥΠΟΥ" ---
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
# Μεγάλη ανάλυση για να "ξεγελάσουμε" το site ότι είμαστε σε PC
chrome_options.add_argument('--window-size=1920,1200') 
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)

# Η ΛΙΣΤΑ (Γραμμένη ακριβώς όπως εμφανίζεται στο site)
# Περιλαμβάνει Αττική, Κάσο, Κάρπαθο, Ρόδο, Σπάρτη
target_stations = [
    "ΕΛΛΗΝΙΚΟ", "ΕΛΕΥΣΙΝΑ", "ΕΛ. ΒΕΝΙΖΕΛΟΣ 03L", "ΜΑΡΚΟΠΟΥΛΟ", 
    "ΜΕΓΑΡΑ", "ΟΑΚΑ", "ΠΑΡΝΗΘΑ", "ΤΑΤΟΪ", "ΒΟΥΛΑ",
    "ΚΑΣΟΣ", "ΚΑΡΠΑΘΟΣ", "ΡΟΔΟΣ", "ΣΠΑΡΤΗ"
]

try:
    print("ΕΚΚΙΝΗΣΗ ΡΙΖΙΚΗΣ ΛΥΣΗΣ...")
    driver.get("https://www.emy.gr/hnms-stations")
    # ΤΕΡΑΣΤΙΑ ΑΝΑΜΟΝΗ για να φορτώσει η βαριά εφαρμογή
    time.sleep(15) 

    # Βίαιο κλείσιμο Cookies
    try:
        driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.textContent.includes('Αποδοχή')) b.click(); })")
        time.sleep(2)
    except: pass

    # Δημιουργία φακέλου ημέρας
    today = datetime.now().strftime("%Y-%m-%d")
    save_path = f"screenshots/{today}"
    os.makedirs(save_path, exist_ok=True)

    for station in target_stations:
        print(f"--- ΕΠΕΞΕΡΓΑΣΙΑ: {station} ---")
        try:
            # --- ΤΟ "ΠΥΡΗΝΙΚΟ" ΟΠΛΟ (BRUTE FORCE CLICK) ---
            # Ψάχνει ΟΛΑ τα στοιχεία της σελίδας. Αν βρει το κείμενο, το πατάει με JS.
            clicked = driver.execute_script(f"""
                var elements = document.querySelectorAll('div, span, a, li, button');
                for (var i = 0; i < elements.length; i++) {{
                    // Ελέγχουμε αν το κείμενο είναι ΑΚΡΙΒΩΣ ίδιο (αγνοώντας κενά)
                    if (elements[i].textContent.trim().toUpperCase() === '{station}') {{
                        elements[i].scrollIntoView({{block: "center"}});
                        elements[i].click();
                        return true;
                    }}
                }}
                return false;
            """)
            
            if not clicked:
                print(f"ΑΠΟΤΥΧΙΑ: Δεν βρέθηκε το στοιχείο για '{station}'")
                continue

            # Αναμονή για να φορτώσει το νέο διάγραμμα
            time.sleep(8) 

            # --- Η ΧΕΙΡΟΥΡΓΙΚΗ ΕΠΕΜΒΑΣΗ ΣΤΟ ΔΙΑΓΡΑΜΜΑ ---
            # Εύρεση δεικτών Max/Min
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
                print("ΑΠΟΤΥΧΙΑ: Το διάγραμμα δεν φόρτωσε δεδομένα.")
                continue

            # Φωτογραφία MAX
            driver.execute_script(f"Highcharts.charts[0].tooltip.refresh(Highcharts.charts[0].series[0].data[{indices['maxIdx']}]);")
            time.sleep(1)
            driver.save_screenshot(f"{save_path}/{station.replace(' ', '_')}_MAX.png")
            print(f"-> Αποθηκεύτηκε MAX")

            # Φωτογραφία MIN
            driver.execute_script(f"Highcharts.charts[0].tooltip.refresh(Highcharts.charts[0].series[0].data[{indices['minIdx']}]);")
            time.sleep(1)
            driver.save_screenshot(f"{save_path}/{station.replace(' ', '_')}_MIN.png")
            print(f"-> Αποθηκεύτηκε MIN")

        except Exception as e:
            print(f"ΣΦΑΛΜΑ στο {station}: {e}")
            # Αν αποτύχει, κάνουμε ένα refresh για να ξεκολλήσει για τον επόμενο
            driver.refresh()
            time.sleep(10)

finally:
    driver.quit()
    print("Η ΔΙΑΔΙΚΑΣΙΑ ΟΛΟΚΛΗΡΩΘΗΚΕ.")
