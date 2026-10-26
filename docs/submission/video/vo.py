# Synthesise each caption line with edge-tts, then lay lines out per scene with pauses.
# Writes vo/<scene>.wav (48 kHz mono) and vo/timing.json (caption start/end per line).
import asyncio, json, os, subprocess, wave
import edge_tts
from script import SCENES, VOICE, RATE

FF = os.environ["FFMPEG"]
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "vo")
os.makedirs(OUT, exist_ok=True)
LEAD, GAP, TAIL = 0.9, 0.45, 1.0  # seconds before first line, between lines, after last


async def say(text, path):
    await edge_tts.Communicate(text, voice=VOICE, rate=RATE).save(path)


def pcm(path):
    raw = subprocess.run([FF, "-v", "error", "-i", path, "-ac", "1", "-ar", "48000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    # Trim leading/trailing near-silence so gaps are ours, not the engine's.
    import numpy as np
    x = np.frombuffer(raw, np.int16)
    loud = np.where(np.abs(x) > 300)[0]
    return x[max(loud[0] - 960, 0): loud[-1] + 2400]


async def main():
    import numpy as np
    timing = {}
    for scene, spec in SCENES.items():
        parts, cues, t = [np.zeros(int(LEAD * 48000), np.int16)], [], LEAD
        for i, line in enumerate(spec["lines"]):
            mp3 = os.path.join(OUT, f"{scene}_{i}.mp3")
            await say(line, mp3)
            x = pcm(mp3)
            d = len(x) / 48000
            cues.append({"text": line, "start": round(t, 3), "end": round(t + d, 3)})
            parts += [x, np.zeros(int(GAP * 48000), np.int16)]
            t += d + GAP
        parts[-1] = np.zeros(int(TAIL * 48000), np.int16)
        y = np.concatenate(parts)
        with wave.open(os.path.join(OUT, f"{scene}.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000); w.writeframes(y.tobytes())
        timing[scene] = {"duration": round(len(y) / 48000, 3), "cues": cues}
        print(scene, timing[scene]["duration"])
    json.dump(timing, open(os.path.join(OUT, "timing.json"), "w"), indent=1)


asyncio.run(main())
