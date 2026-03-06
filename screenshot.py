from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
from datetime import datetime

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,3000')

# SSL Bypass
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.accept_insecure_certs = True

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

driver = webdriver.Chrome(options=chrome_options)
target_stations = ["ΕΛΛΗΝΙΚΟ", "ΚΑΣΟΣ", "ΣΠΑΡΤΗ"]

try:
    print("--- ΕΚΚΙΝΗΣΗ: ZERO BASE API INJECTION ---")
    driver.get("https://www.emy.gr/hnms-stations")
    time.sleep(15) 

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(f"screenshots/{today}", exist_ok=True)

    # Απόλυτος καθαρισμός οθόνης
    driver.execute_script("""
        document.querySelectorAll('*').forEach(el => {
            var s = window.getComputedStyle(el);
            if(s.position === 'fixed' || s.position === 'sticky' || el.id.includes('cookie')) el.remove();
        });
    """)
    time.sleep(2)

    for station in target_stations:
        print(f"\n[{station}] Ανάλυση...")
        
        try:
            # 1. THE LEAFLET INJECTION (Απόλυτη Ακρίβεια Πινέζας)
            if station != "ΕΛΛΗΝΙΚΟ":
                js_leaflet = f"""
                var container = document.querySelector('.leaflet-container');
                if(!container) return false;
                var map = null;
                for (var key in container) {{
                    if (key.startsWith('__leaflet_')) {{
                        map = container[key];
                        if (map._map) map = map._map;
                        break;
                    }}
                }}
                if(!map) return false;
                
                var found = false;
                map.eachLayer(function(layer) {{
                    if(layer._popup && typeof layer._popup._content === 'string') {{
                        if(layer._popup._content.toUpperCase().includes('{station}')) {{
                            layer.fire('click'); // Ανοίγει ακαριαία την πινέζα
                            found = true;
                        }}
                    }}
                }});
                return found;
                """
                found = driver.execute_script(js_leaflet)
                
                if not found:
                    print(f"[{station}] Σφάλμα: Δεν βρέθηκε στη βάση δεδομένων του χάρτη.")
                    driver.save_screenshot(f"screenshots/{today}/ERROR_PIN_{station}.png")
                    continue
                else:
                    print(f"[{station}] Η πινέζα άνοιξε ακαριαία μέσω API.")
                    time.sleep(2) 
            
            # 2. ΣΚΡΟΛ ΚΑΤΩ ΣΤΟ ΔΙΑΓΡΑΜΜΑ
            driver.execute_script("window.scrollBy(0, 850);")
            time.sleep(6) 
            
            # 3. THE HIGHCHARTS DUAL TRIGGER (API + Virtual Mouse)
            def trigger_hover(point_type):
                js_hover = f"""
                var chart = Highcharts.charts.find(c => c && c.series && c.series[0].points);
                if(!chart) return false;
                var points = chart.series[0].points;
                var target = null;
                
                for(var i=0; i<points.length; i++) {{
                    if(points[i].y !== null) {{
                        if(target === null) target = points[i];
                        else if('{point_type}' === 'max' && points[i].y > target.y) target = points[i];
                        else if('{point_type}' === 'min' && points[i].y < target.y) target = points[i];
                    }}
                }}
                if(!target) return false;

                // Ενεργοποίηση API
                if (chart.tooltip.shared) {{ chart.tooltip.refresh([target]); }} 
                else {{ chart.tooltip.refresh(target); }}
                if(chart.xAxis[0]) chart.xAxis[0].drawCrosshair(null, target);
                target.setState('hover');
                
                // Δημιουργία Εικονικού Ποντικιού
                var rect = chart.container.getBoundingClientRect();
                var clientX = rect.left + chart.plotLeft + target.plotX;
                var clientY = rect.top + chart.plotTop + target.plotY;
                var evt = new MouseEvent('mousemove', {{
                    clientX: clientX, clientY: clientY, bubbles: true, cancelable: true, view: window
                }});
                chart.container.dispatchEvent(evt);
                
                return true;
                """
                return driver.execute_script(js_hover)

            # MAX Φωτογραφία
            if trigger_hover('max'):
                time.sleep(1.5)
                driver.save_screenshot(f"screenshots/{today}/{station}_MAX.png")
            else:
                driver.save_screenshot(f"screenshots/{today}/ERROR_CHART_{station}_MAX.png")

            # MIN Φωτογραφία
            if trigger_hover('min'):
                time.sleep(1.5)
                driver.save_screenshot(f"screenshots/{today}/{station}_MIN.png")
            else:
                driver.save_screenshot(f"screenshots/{today}/ERROR_CHART_{station}_MIN.png")

            print(f"[{station}] ΟΛΟΚΛΗΡΩΘΗΚΕ ΕΠΙΤΥΧΩΣ.")

            # Καθαρισμός για τον επόμενο
            driver.refresh()
            time.sleep(8)
            driver.execute_script("""
                document.querySelectorAll('*').forEach(el => {
                    var s = window.getComputedStyle(el);
                    if(s.position === 'fixed' || s.position === 'sticky' || el.id.includes('cookie')) el.remove();
                });
            """)

        except Exception as e:
            print(f"[{station}] ΣΦΑΛΜΑ ΣΥΣΤΗΜΑΤΟΣ: {e}")
            driver.save_screenshot(f"screenshots/{today}/CRASH_{station}.png")
            driver.refresh()
            time.sleep(8)
            continue 

finally:
    driver.quit()
    print("Η Zero Base διαδικασία τερματίστηκε.")
