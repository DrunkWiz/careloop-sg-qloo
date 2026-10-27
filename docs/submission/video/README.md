# Qloo demo video pipeline

`careloop-qloo-launch-video.mp4` is the general film (`CareLoop-SG-demo-general-v2.mp4`, made with Remotion) with two Qloo scenes cut in. On the end card, the links now read careloop-sg-qloo.onrender.com and github.com/DrunkWiz/careloop-sg-qloo, and "Powered by Qloo Taste AI" sits under them. Everything else is the original film, untouched.

| Time | What |
|---|---|
| 0:00 – 1:38 | Original film |
| 1:38 – 2:09 | New: "Good days, planned around him." then "His health comes first." (Qloo picks, checked against medicine, BP and weather) |
| 2:09 – 5:47 | Original film |
| 5:47 – 6:11 | New: "Picked for him. Safe for him." (the 38-persona taste benchmark) |
| 6:11 – 6:26 | Original ending with the new links, the Qloo line and a 1.5 s hold |

## How it is built

1. `capture_phone.py` takes phone screenshots of the running web app (mock mode, `npm run dev` on :5174).
2. `script.py` holds the new voice lines; `vo.py` voices them with edge-tts (`en-US-JennyNeural`, -14%) and writes caption timings.
3. `scenes.html` draws the new scenes in the film's style (Instrument Serif, Inter, sampled colours); `render.py` renders them frame by frame at 30 fps.
4. `overlay.py` makes the end-card layers: clean background over the old links (from the 329.0 s frame, before they appear), the new links in Inter at the old size and place, and the Qloo line.
5. `assemble.py` cuts it all together. Cuts sit in voice gaps on still frames. The film's music is ducked under a centre-panned voice, so its side channel (L-R) is music only; that is the bed under the new lines. Loudness is matched to the original.

Inputs `assemble.py` expects: the original film at `../ref/ref.mp4` relative to the scripts, and `FFMPEG` set to the ffmpeg path.

## Known gaps

- The original narrator's voice is not an Edge voice, so the new lines use the closest one (Jenny). `voice-check.m4a` plays an original line, then a new one.
- The benchmark baselines are scripted stand-ins, not live model runs, and the video says so on screen. All people are synthetic.

## Gallery images

`gallery.py` and `gallery.html` make the 3:2 screenshots in `../gallery/` (shown in the main README) from the running web app: `python gallery.py ../gallery` while `npm run dev` runs on :5174.
