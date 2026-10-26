# Cut the Qloo inserts into the reference film and build the matching soundtrack.
#   ref[0, 98.3] ~ A ~ ref[98.95, 317.4] ~ B | ref[318.2, end] + "Powered by Qloo" + 1.5 s hold
# Cuts sit in voice gaps on still frames. The reference's music is ducked under a centre-panned
# voice, so the side channel (L-R) is music only; that is the bed under the new lines.
import json, os, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FF = os.environ["FFMPEG"]
REF = os.path.join(HERE, "..", "ref", "ref.mp4")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "render", "careloop-qloo-launch-video.mp4")
SR = 48000
C1, R2S, C2, R3S = 98.3, 98.95, 317.4, 318.32
# The reference slides the family phones in from 98.67 to 99.57 s while its voice starts at 99.1 s.
# Picture resumes on the settled frame (held until the sound catches up) so the two stay in sync.
R2V = 99.57
XA_IN, XA_OUT, XB_IN, HOLD = 0.5, 0.5, 0.6, 1.5
END_CARD = 330.0  # ref time the end card's URLs have settled
URL_CLEAN, URL_IN = 329.0, 329.27  # old URLs absent at 329.0; they fade in over 0.5 s from 329.27

tm = json.load(open(os.path.join(HERE, "vo", "timing.json")))
DA = tm["A1"]["duration"] + tm["A2"]["duration"]
DB = tm["B"]["duration"]


def probe(p):
    probe_exe = os.path.join(os.path.dirname(FF), os.path.basename(FF).replace("ffmpeg", "ffprobe"))
    return float(subprocess.run([probe_exe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)


def read_wav(p, ch):
    raw = subprocess.run([FF, "-v", "error", "-i", p, "-ac", str(ch), "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32).reshape(-1, ch) / 32768


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def smooth(x, sec):
    """Centred moving average via a cumulative sum (np.convolve here took minutes)."""
    n = max(1, int(sec * SR))
    c = np.concatenate([[0.0], np.cumsum(np.asarray(x, np.float64))])
    i = np.arange(len(x))
    lo, hi = np.clip(i - n // 2, 0, len(x)), np.clip(i - n // 2 + n, 0, len(x))
    return ((c[hi] - c[lo]) / n).astype(np.float32)


def speech_rms(x):
    """RMS over 50 ms frames loud enough to be speech (within 15 dB of the loudest)."""
    n = SR // 20
    f = x[: len(x) // n * n].reshape(-1, n)
    r = np.sqrt((f ** 2).mean(1)) + 1e-9
    keep = 20 * np.log10(r) > 20 * np.log10(r.max()) - 15
    return 20 * np.log10(np.sqrt((f[keep] ** 2).mean()))


ref = read_wav(REF, 2)
M, S = ref.mean(1), (ref[:, 0] - ref[:, 1]) / 2
# Reference levels: voice (mid, during speech) and music in voice gaps (side channel).
ref_voice_db = speech_rms(M[int(12 * SR): int(32 * SR)])
GAPS = [(32.9, 35.1), (36.0, 38.7), (48.6, 51.7), (59.8, 62.3)]
side_gap_db = rms_db(np.concatenate([S[int(a * SR): int(b * SR)] for a, b in GAPS]))
mid_gap_db = rms_db(np.concatenate([M[int(a * SR): int(b * SR)] for a, b in GAPS]))
print(f"ref voice {ref_voice_db:.1f} dB, music in gaps: mid {mid_gap_db:.1f} side {side_gap_db:.1f}")


def bed(src_t, dur, vo):
    """Side-channel music from the reference, levelled, then ducked under the new voice."""
    s = S[int(src_t * SR): int(src_t * SR) + len(vo)].copy()
    if len(s) < len(vo):
        s = np.pad(s, (0, len(vo) - len(s)))
    env = np.sqrt(smooth(s ** 2, 0.6)) + 1e-6
    target = 10 ** (mid_gap_db / 20)  # whole-mix music level in the reference's gaps
    s *= np.clip(target / env, 0, 10 ** (20 / 20))
    active = smooth((np.abs(vo) > 0.02).astype(np.float32), 0.25) > 0.05
    duck = smooth(np.where(active, 10 ** (-12 / 20), 1.0).astype(np.float32), 0.3)
    return s * duck


def insert_audio(vo_wavs, src_t, dur):
    vo = np.zeros(int(round(dur * SR)), np.float32)
    t = 0.0
    for p, d in vo_wavs:
        x = read_wav(p, 1)[:, 0]
        i = int(round(t * SR)); vo[i: i + len(x)] += x[: len(vo) - i]
        t += d
    vo *= 10 ** ((ref_voice_db - speech_rms(vo)) / 20)
    mix = vo + bed(src_t, dur, vo)
    return np.stack([mix, mix], 1)


def xfade(a, b, sec):
    n = int(round(sec * SR))
    if n == 0:
        return np.concatenate([a, b])
    w = np.linspace(0, np.pi / 2, n)[:, None]
    return np.concatenate([a[:-n], a[-n:] * np.cos(w) + b[:n] * np.sin(w), b[n:]])


seg = lambda a, b=None: ref[int(round(a * SR)): (int(round(b * SR)) if b else len(ref))]
A = insert_audio([(os.path.join(HERE, "vo", "A1.wav"), tm["A1"]["duration"]), (os.path.join(HERE, "vo", "A2.wav"), tm["A2"]["duration"])], C1, DA)
# The reference ends 15 s after C2, so B's bed is the music just before the cut.
B = insert_audio([(os.path.join(HERE, "vo", "B.wav"), DB)], C2 - DB, DB)
tail = seg(R3S)
ext = np.stack([bed(328.4, HOLD + 0.2, np.zeros(int((HOLD + 0.2) * SR), np.float32))] * 2, 1)
tail = xfade(tail, ext, 0.2)
audio = xfade(xfade(xfade(seg(0, C1), A, XA_IN), seg(R2S, C2), XA_OUT), B, XB_IN)
audio = np.concatenate([audio, tail])
fade = int(2.2 * SR)
audio[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 1.5
wav = os.path.join(HERE, "render", "soundtrack.wav")
with wave.open(wav, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
print(f"audio {len(audio) / SR:.2f}s, overall {rms_db(audio):.1f} dB vs ref {rms_db(ref):.1f} dB")

# Video
A_mp4, B_mp4 = os.path.join(HERE, "render", "A.mp4"), os.path.join(HERE, "render", "B.mp4")
DA_v, DB_v = probe(A_mp4), probe(B_mp4)
norm = "fps=30,format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS"
o1 = C1 - XA_IN
o2 = o1 + DA_v - XA_OUT
o3 = o2 + (C2 - R2S) - XB_IN
card = END_CARD - R3S
fc = ";".join([
    f"[0:v]trim=0:{C1},{norm}[r1]",
    f"[0:v]trim={R2V}:{C2},{norm},tpad=start_mode=clone:start_duration={R2V - R2S:.3f}[r2]",
    f"[0:v]trim={R3S},{norm}[r3raw]",
    f"[1:v]{norm}[a]", f"[2:v]{norm}[b]",
    f"[3:v]format=rgba,fade=in:st={card + 0.3}:d=0.6:alpha=1[ov]",
    # Old URLs are covered by clean background, and the new ones fade in when the old ones did.
    f"[5:v]format=rgba[bg]",
    f"[6:v]format=rgba,fade=in:st={URL_IN - R3S:.3f}:d=0.5:alpha=1[urls]",
    f"[r3raw][bg]overlay=shortest=1:enable='gte(t,{URL_CLEAN - R3S:.3f})'[r3a]",
    f"[r3a][urls]overlay=shortest=1[r3b]",
    f"[r3b][ov]overlay=shortest=1,tpad=stop_mode=clone:stop_duration={HOLD},format=yuv420p[r3]",
    f"[r1][a]xfade=transition=fade:duration={XA_IN}:offset={o1}[x1]",
    f"[x1][r2]xfade=transition=fade:duration={XA_OUT}:offset={o2}[x2]",
    f"[x2][b]xfade=transition=fade:duration={XB_IN}:offset={o3}[x3]",
    "[x3][r3]concat=n=2:v=1:a=0[v]",
])
tail_len = probe(REF) - R3S
subprocess.run([FF, "-v", "error", "-y", "-i", REF, "-i", A_mp4, "-i", B_mp4,
                "-loop", "1", "-framerate", "30", "-t", f"{tail_len:.3f}", "-i", os.path.join(HERE, "render", "endcard_overlay.png"),
                "-i", wav,
                "-loop", "1", "-framerate", "30", "-t", f"{tail_len:.3f}", "-i", os.path.join(HERE, "render", "endcard_bg.png"),
                "-loop", "1", "-framerate", "30", "-t", f"{tail_len:.3f}", "-i", os.path.join(HERE, "render", "endcard_urls.png"),
                "-filter_complex", fc, "-map", "[v]", "-map", "4:a",
                "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest",
                "-metadata", "title=CareLoop SG, powered by Qloo", OUT], check=True)
print("wrote", OUT, f"{probe(OUT):.2f}s", f"(A in at {o1 + XA_IN:.2f}s, B in at {o3 + XB_IN:.2f}s)")
