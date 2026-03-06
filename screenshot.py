from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080')
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)

try:
    print("Μπαίνω στο site για να δω τι ακριβώς μου κρύβουν...")
    driver.get("https://www.emy.gr/hnms-stations")
    
    # Περιμένουμε 15 δεύτερα για να φορτώσει ή να βγάλει το Captcha
    time.sleep(15) 
    
    # Φτιάχνουμε τον φάκελο screenshots αν δεν υπάρχει
    os.makedirs("screenshots", exist_ok=True)
    
    # Τραβάμε τη φωτογραφία
    driver.save_screenshot("screenshots/ROBOT_VISION.png")
    print("Η φωτογραφία τραβήχτηκε! Ανεβαίνει στο GitHub.")

finally:
    driver.quit()
