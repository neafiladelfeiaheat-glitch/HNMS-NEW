from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080')
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)

try:
    print("Ξεκινάω την κατασκοπεία στο HNMS...")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(10) # Περιμένουμε να φορτώσει καλά

    # Ψάχνουμε όλα τα στοιχεία που μοιάζουν με λίστα σταθμών
    stations = driver.find_elements(By.CSS_SELECTOR, "div") 
    
    print("--- ΛΙΣΤΑ ΣΤΑΘΜΩΝ ΟΠΩΣ ΤΗΝ ΒΛΕΠΕΙ ΤΟ ΡΟΜΠΟΤ ---")
    found = False
    for s in stations:
        text = s.text.strip()
        # Φιλτράρουμε για να πιάσουμε μόνο τα ονόματα (Αττική, Κάσος, κτλ)
        if text and len(text) > 3 and len(text) < 30 and "\n" not in text:
            if "Αθήνα" in text or "Ελευσ" in text or "Κάσος" in text or "Κάρπαθος" in text or "Ρόδος" in text or "Σπάρτη" in text:
                print(f"ΒΡΕΘΗΚΕ: '{text}'")
                found = True
                
    if not found:
        print("Δεν βρήκα τα ονόματα! Το site ίσως αργεί να φορτώσει ή κρύβει τη λίστα.")

finally:
    driver.quit()
