from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
import sys
from datetime import datetime

if len(sys.argv) < 3: sys.exit(1)
station_id, station_name = sys.argv[1], sys.argv[2]

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--window-size=1920,2000')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.accept_insecure_certs = True
driver = webdriver.Chrome(options=chrome_options)

try:
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(15)

    # 1. ΕΠΙΛΟΓΗ ΣΤΑΘΜΟΥ ΜΕ ΤΟ "ΑΟΡΑΤΟ ΔΑΧΤΥΛΟ" (JS Trigger)
    # Καλούμε την εσωτερική συνάρτηση της ΕΜΥ απευθείας
    driver.execute_script(f"if(window.selectStation) {{ selectStation({station_id}); }}")
    time.sleep(10) # Χρόνος για να φορτώσει το διάγραμμα

    # 2. ΦΥΣΙΚΟ HOVER ΜΕ ACTION CHAINS
    js_coords = """
    var chart = Highcharts.charts.find(c => c && c.series[0].points);
    if(!chart) return null;
    var pts = chart.series[0].points.filter(p => p.y !== null);
    var max = pts.reduce((a, b) => a.y > b.y ? a : b);
    var min = pts.reduce((a, b) => a.y < b.y ? a : b);
    return {
        maxX: max.plotX + chart.plotLeft, maxY: max.plotY + chart.plotTop,
        minX: min.plotX + chart.plotLeft, minY: min.plotY + chart.plotTop
    };
    """
    coords = driver.execute_script(js_coords)
    
    if coords:
        today = datetime.now().strftime("%Y-%m-%d")
        os.makedirs(f"screenshots/{today}", exist_ok=True)
        chart_div = driver.find_element(By.CSS_SELECTOR, ".highcharts-container")
        actions = ActionChains(driver)

        # MAX Hover
        actions.move_to_element_with_offset(chart_div, coords['maxX'], coords['maxY']).perform()
        time.sleep(2)
        driver.save_screenshot(f"screenshots/{today}/{station_name}_MAX.png")

        # MIN Hover
        actions.move_to_element_with_offset(chart_div, coords['minX'], coords['minY']).perform()
        time.sleep(2)
        driver.save_screenshot(f"screenshots/{today}/{station_name}_MIN.png")
    else:
        # Screenshot αποτυχίας για debug
        driver.save_screenshot(f"ERROR_CHART_{station_name}.png")

finally:
    driver.quit()
