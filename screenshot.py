from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
import sys
from datetime import datetime

# Λαμβάνουμε το ID και το Όνομα του σταθμού ως ορίσματα από το GitHub
if len(sys.argv) < 3:
    print("Σφάλμα: Απαιτούνται ID και Όνομα σταθμού.")
    sys.exit(1)

station_id = sys.argv[1]
station_name = sys.argv[2]

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080') # Δεν χρειάζεται γίγαντας
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.accept_insecure_certs = True
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)

try:
    print(f"[{station_name}] Επεξεργασία (ID: {station_id})...")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(12) 

    today = datetime.now().strftime("%Y-%m-%d")
    save_path = f"screenshots/{today}"
    os.makedirs(save_path, exist_ok=True)

    # 1. Σκοτώνουμε τα cookies
    driver.execute_script("""
        document.querySelectorAll('*').forEach(el => {
            var s = window.getComputedStyle(el);
            if(s.position === 'fixed' || s.position === 'sticky' || el.id.includes('cookie')) el.remove();
        });
    """)
    time.sleep(1)

    # 2. ΤΟ ΜΑΓΙΚΟ ID: Επιλογή σταθμού απευθείας από το dropdown
    js_select_station = f"""
    try {{
        var select = document.querySelector('select.form-control');
        if (select) {{
            select.value = '{station_id}';
            select.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return true;
        }}
        return false;
    }} catch(e) {{ return false; }}
    """
    
    success_selection = driver.execute_script(js_select_station)
    
    if not success_selection:
        print(f"[{station_name}] Σφάλμα: Δεν μπόρεσα να επιλέξω τον σταθμό με ID {station_id}.")
        driver.save_screenshot(f"{save_path}/ERROR_{station_name}_SELECTION.png")
        sys.exit(1)

    # 3. Περιμένουμε το διάγραμμα Highcharts (δεν χρειάζεται σκρολ πια, είναι ορατό)
    time.sleep(8) 
    
    # 4. ΤΟ ΑΠΟΛΥΤΟ NATIVE JS HOVER
    js_native_hover = """
    try {
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
        var rect = chart.container.getBoundingClientRect();
        var clientX = rect.left + chart.plotLeft + target.plotX;
        var clientY = rect.top + chart.plotTop + target.plotY;
        var evt = new MouseEvent('mousemove', {
            clientX: clientX, clientY: clientY, bubbles: true, cancelable: true, view: window
        });
        chart.container.dispatchEvent(evt);
        return true;
    } catch(e) { return false; }
    """

    # Φωτογραφία MAX
    if driver.execute_script(js_native_hover, True):
        time.sleep(1.5)
        driver.save_screenshot(f"{save_path}/{station_name}_MAX.png")
    else:
        driver.save_screenshot(f"{save_path}/ERROR_{station_name}_MAX.png")

    # Φωτογραφία MIN
    if driver.execute_script(js_native_hover, False):
        time.sleep(1.5)
        driver.save_screenshot(f"{save_path}/{station_name}_MIN.png")
    else:
        driver.save_screenshot(f"{save_path}/ERROR_{station_name}_MIN.png")

    print(f"[{station_name}] Ολοκληρώθηκε ΕΠΙΤΥΧΩΣ.")

except Exception as e:
    print(f"[{station_name}] Κράσαρε: {e}")
    # Δεν βγάζουμε screenshot κράσαρματος εδώ για να μην γεμίζει ο φάκελος
finally:
    driver.quit()
