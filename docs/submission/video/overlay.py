# End-card overlays for the reference film's last scene (1920x1080 PNGs):
#   render/endcard_bg.png    clean background over the old URLs (taken from the 329.0 s frame, before they appear)
#   render/endcard_urls.png  the new URLs, drawn in Inter at the size and place of the old ones
#   render/endcard_overlay.png  "POWERED BY QLOO TASTE AI"
import base64, os, subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

HERE = os.path.dirname(os.path.abspath(__file__))
FF = os.environ["FFMPEG"]
REF = os.path.join(HERE, "..", "ref", "ref.mp4")
OUT = os.path.join(HERE, "render")
URLS = ["careloop-sg-qloo.onrender.com", "github.com/DrunkWiz/careloop-sg-qloo"]
# Measured on the reference's last frame: old line 1 "careloop-sg.onrender.com" inks x 772-1146, y 623-650;
# line 2 inks from y 673. Text colour sampled near #1c2b1e.
OLD1, OLD1_W, TOP1, TOP2 = "careloop-sg.onrender.com", 1146 - 772 + 1, 623, 673
PATCH = (600, 720)  # rows covered by the clean background

bg_png = os.path.join(OUT, "endcard_bg_src.png")
subprocess.run([FF, "-v", "error", "-y", "-ss", "329.0", "-i", REF, "-frames:v", "1", bg_png], check=True)

HTML = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=block" rel="stylesheet">
<style>html,body{margin:0;width:1920px;height:1080px;background:transparent;overflow:hidden}
canvas{position:absolute;left:0;top:0}
#k{position:absolute;left:0;right:0;top:752px;text-align:center;font:500 22px Inter;letter-spacing:.16em;color:#5c745c}</style>
</head><body><canvas id="c" width="1920" height="1080"></canvas><div id="k">POWERED BY QLOO TASTE AI</div></body></html>"""
path = os.path.join(HERE, "overlay.html")
open(path, "w", encoding="utf-8").write(HTML)

DRAW = """
const [mode, old1, oldW, top1, top2, urls, bgUrl, y0, y1] = arguments;
const c = document.getElementById('c'), x = c.getContext('2d');
x.clearRect(0, 0, 1920, 1080);
document.getElementById('k').style.display = mode === 'k' ? '' : 'none';
if (mode === 'bg') {
  const img = new Image(); img.src = bgUrl; return img.decode().then(() => x.drawImage(img, 0, y0, 1920, y1 - y0, 0, y0, 1920, y1 - y0)).then(() => 'bg');
}
if (mode !== 'urls') return 'k';
// Size: the old first line's ink width at that size must match the measured width.
let s = 20; for (; s < 40; s += 0.05) { x.font = `400 ${s}px Inter`; if (x.measureText(old1).width >= oldW) break; }
x.font = `400 ${s}px Inter`; x.fillStyle = '#1c2b1e'; x.textAlign = 'center';
const asc = x.measureText(old1).actualBoundingBoxAscent;
x.fillText(urls[0], 960, top1 + asc);
x.fillText(urls[1], 960, top2 + x.measureText('github.com/DrunkWiz/careloop-sg').actualBoundingBoxAscent);
return s;
"""

o = Options(); o.add_argument("--headless=new"); o.add_argument("--allow-file-access-from-files")
d = webdriver.Chrome(options=o)
try:
    d.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {"width": 1920, "height": 1080, "deviceScaleFactor": 1, "mobile": False})
    d.execute_cdp_cmd("Emulation.setDefaultBackgroundColorOverride", {"color": {"r": 0, "g": 0, "b": 0, "a": 0}})
    d.get("file:///" + path.replace("\\", "/"))
    d.execute_async_script("const cb=arguments[0]; document.fonts.load('400 28px Inter').then(()=>document.fonts.ready).then(()=>setTimeout(cb,500));")
    bg_url = "file:///" + bg_png.replace("\\", "/")
    for mode, name in [("bg", "endcard_bg.png"), ("urls", "endcard_urls.png"), ("k", "endcard_overlay.png")]:
        r = d.execute_script(DRAW, mode, OLD1, OLD1_W, TOP1, TOP2, URLS, bg_url, *PATCH)
        shot = d.execute_cdp_cmd("Page.captureScreenshot", {"format": "png"})
        open(os.path.join(OUT, name), "wb").write(base64.b64decode(shot["data"]))
        print(name, r)
finally:
    d.quit()
