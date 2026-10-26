# Full-page phone captures of the running web app (mock mode) for the video's phone frames.
import base64, os, sys, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE = "http://localhost:5174"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screens")
os.makedirs(OUT, exist_ok=True)
SHOTS = {
    "senior_home": "/senior?senior=tan",
    "family_activities": "/care/family/activities?contact=tan-weiling",
}

o = Options()
o.add_argument("--headless=new")
o.add_argument("--hide-scrollbars")
d = webdriver.Chrome(options=o)
try:
    for name, path in SHOTS.items():
        d.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 3, "mobile": True})
        d.get(BASE + path)
        time.sleep(3)
        h = d.execute_script("return document.documentElement.scrollHeight")
        # One phone-sized shot too, for the fixed bottom tab bar.
        r = d.execute_cdp_cmd("Page.captureScreenshot", {"format": "png"})
        open(os.path.join(OUT, name + "_view.png"), "wb").write(base64.b64decode(r["data"]))
        # A tall viewport keeps fixed bars at the bottom instead of painting them mid-page.
        d.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {"width": 390, "height": h, "deviceScaleFactor": 3, "mobile": True})
        time.sleep(1.5)
        r = d.execute_cdp_cmd("Page.captureScreenshot", {"format": "png"})
        open(os.path.join(OUT, name + ".png"), "wb").write(base64.b64decode(r["data"]))
        print(name, h)
finally:
    d.quit()
