# Render scenes.html frame by frame (30 fps, 1920x1080) into ProRes-free intermediate MP4s.
# Usage: python render.py A B E      or   python render.py --still A 5.0 out.png
import base64, json, os, subprocess, sys, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

HERE = os.path.dirname(os.path.abspath(__file__))
FF = os.environ["FFMPEG"]
FPS = 30
timing = json.load(open(os.path.join(HERE, "vo", "timing.json")))
open(os.path.join(HERE, "vo", "timing.js"), "w").write("window.TIMING = " + json.dumps(timing) + ";")
DUR = {"A": timing["A1"]["duration"] + timing["A2"]["duration"], "B": timing["B"]["duration"], "E": 4.0}


def driver():
    o = Options()
    o.add_argument("--headless=new")
    o.add_argument("--hide-scrollbars")
    o.add_argument("--allow-file-access-from-files")
    d = webdriver.Chrome(options=o)
    d.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {"width": 1920, "height": 1080, "deviceScaleFactor": 1, "mobile": False})
    d.get("file:///" + os.path.join(HERE, "scenes.html").replace("\\", "/"))
    d.execute_async_script("const cb = arguments[0]; document.fonts.ready.then(() => setTimeout(cb, 800));")
    assert d.execute_script("return document.fonts.check('118px \"Instrument Serif\"') && document.fonts.check('30px Inter')"), "fonts not loaded"
    return d


def shot(d, scene, t):
    d.execute_script(f"setT('{scene}', {t})")
    r = d.execute_cdp_cmd("Page.captureScreenshot", {"format": "png"})
    return base64.b64decode(r["data"])


if __name__ == "__main__":
    d = driver()
    try:
        if sys.argv[1] == "--still":
            open(sys.argv[4], "wb").write(shot(d, sys.argv[2], float(sys.argv[3])))
            sys.exit()
        for scene in sys.argv[1:]:
            n = round(DUR[scene] * FPS)
            out = os.path.join(HERE, "render", f"{scene}.mp4")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            enc = subprocess.Popen([FF, "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "png", "-i", "-",
                                    "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
            t0 = time.time()
            for i in range(n):
                enc.stdin.write(shot(d, scene, i / FPS))
            enc.stdin.close(); enc.wait()
            print(scene, n, "frames", round(time.time() - t0), "s")
    finally:
        d.quit()
