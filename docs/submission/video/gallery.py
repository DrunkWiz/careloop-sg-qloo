# Devpost gallery: 3:2 images (2400x1600 JPG) from the running web app (mock mode, `npm run dev` on :5174).
# Phone screens are captured phone-sized, scrolled to the part that matters, and framed like the video.
# Desktop screens are captured at 1200x800, which is already 3:2.
# Usage: python gallery.py <out_dir>
import base64, io, json, os, sys, time
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE = "http://localhost:5174"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1])
os.makedirs(OUT, exist_ok=True)

# name, path, text to scroll to (None = top), kicker, headline, sub
PHONE = [
    ("01-senior-check-in", "/senior?senior=tan", "Your day", "For seniors",
     "One big button.", "Hold to talk in English, Singlish or Mandarin. Thirty seconds and it's done."),
    ("02-qloo-good-days", "/senior?senior=tan", "Haze today", "Powered by Qloo Taste AI",
     "Good days,\nplanned around him.", "Qloo turns what he loves into nearby picks. On a haze day, everything moves indoors."),
    ("03-qloo-health-first", "/care/family/activities?contact=tan-weiling", "CareLoop + Qloo taste graph", "Qloo + safety rules",
     "His health\ncomes first.","Every Qloo pick is checked against his medicines, his conditions and today's weather."),
    ("04-red-flag", "/care/family?contact=tan-weiling&scenario=redflag", None, "For families",
     "Some moments\ncan't wait.","A red flag skips the rota and reaches every family member at once."),
    ("05-his-own-usual", "/care/family/health?contact=tan-weiling", "Blood pressure", "For families",
     "His own usual,\nday by day.","Readings against his own normal from the last 30 days, not one fixed line for everyone."),
    ("06-memory-lane", "/senior?senior=tan", "Memory Lane", "Powered by Qloo Taste AI",
     "Memory Lane.", "A daily story prompt from his own nostalgia, saved as keepsakes for the family."),
]
DESK = [
    ("07-centre-caseload", "/care/aac?worker=aac-siti", None),
    ("08-taste-benchmark", "/eval/taste", None),
    ("09-judge-view", "/pitch", None),
]

SCROLL = """
const [text] = arguments;
const el = [...document.querySelectorAll('h1,h2,h3,p,strong,summary,.sa-card-label')].find(e => e.textContent.trim().startsWith(text));
if (!el) return false;
window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - 76);
return true;
"""


def driver():
    o = Options(); o.add_argument("--headless=new"); o.add_argument("--hide-scrollbars"); o.add_argument("--allow-file-access-from-files")
    return webdriver.Chrome(options=o)


def png(d):
    return Image.open(io.BytesIO(base64.b64decode(d.execute_cdp_cmd("Page.captureScreenshot", {"format": "png"})["data"])))


d = driver()
try:
    shots = {}
    for name, path, text, *_ in PHONE:
        d.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 3, "mobile": True})
        d.get(BASE + path); time.sleep(3)
        if text and not d.execute_script(SCROLL, text):
            raise SystemExit(f"{name}: no element starting with {text!r}")
        time.sleep(0.8)
        p = os.path.join(OUT, f"_{name}.png"); png(d).save(p); shots[name] = p
    for name, path, _ in DESK:
        d.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {"width": 1200, "height": 800, "deviceScaleFactor": 2.4, "mobile": False})
        d.get(BASE + path); time.sleep(3.5)
        png(d).convert("RGB").save(os.path.join(OUT, f"{name}.jpg"), quality=90)

    # Frame the phone shots, 1500x1000 CSS px at 1.6x = 2400x1600.
    d.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {"width": 1500, "height": 1000, "deviceScaleFactor": 1.6, "mobile": False})
    d.get("file:///" + os.path.join(HERE, "gallery.html").replace("\\", "/"))
    d.execute_async_script("const cb=arguments[0]; document.fonts.ready.then(()=>setTimeout(cb,600));")
    for name, _, _, kicker, head, sub in PHONE:
        src = "file:///" + shots[name].replace("\\", "/")
        d.execute_async_script("const cb=arguments[arguments.length-1]; show(arguments[0]).then(cb);",
                               {"kicker": kicker, "head": head, "sub": sub, "src": src})
        png(d).convert("RGB").save(os.path.join(OUT, f"{name}.jpg"), quality=90)
        os.remove(shots[name])
finally:
    d.quit()
for f in sorted(os.listdir(OUT)):
    p = os.path.join(OUT, f); print(f, Image.open(p).size, f"{os.path.getsize(p) / 1e6:.2f} MB")
