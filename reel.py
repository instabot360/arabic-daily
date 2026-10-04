"""Render a 9.5s vertical Reel (1080x1920) for one word using Pillow + ffmpeg."""
import asyncio, os, re, subprocess, tempfile
from PIL import Image, ImageDraw
import render as R

W, H, FPS, DUR = 1080, 1920, 24, 11.0

def _bg():
    img = Image.new("RGB", (W, H), R.BG1)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(R.BG1[i] + (R.BG2[i] - R.BG1[i]) * t) for i in range(3)))
    d.rounded_rectangle((40, 150, W - 40, H - 330), 36, outline=R.GOLD, width=3)
    return img

def _layer(draw_fn):
    """Pre-render one element on a transparent full-frame layer."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    return layer

def _text(xy, text, kind, size, fill, max_w=900, rtl=False):
    return lambda d: R.draw_fit(d, xy, text, kind, size, fill, max_w, rtl)

def _plain(xy, text, kind, size, fill):
    return lambda d: d.text(xy, text, font=R.font(kind, size), fill=fill, anchor="mm")

def build_elements(w, level, day, handle):
    """(layer, start, end_or_None, fade_in, fade_out)."""
    E = []
    def add(fn, s, e=None, fi=0.5, fo=0.4):
        E.append((_layer(fn), s, e, fi, fo))
    add(_plain((W // 2, 330), "WORD OF THE DAY", "bold", 44, R.GOLD), 0.0)
    add(_plain((W // 2, 395), f"Day {day}  •  {level}", "reg", 32, R.MUTED), 0.2)
    add(_text((W // 2, 640), w["arabic"], "arabic", 300, R.CREAM, 880, True), 0.5)
    add(_plain((W // 2, 880), w["transliteration"], "reg", 56, R.GOLD), 1.3)
    add(_plain((W // 2, 1200), "What does it mean?", "bold", 54, R.CREAM), 2.6, 6.6)
    for n, t in ((3, 3.6), (2, 4.6), (1, 5.6)):   # one full second per number
        add(_plain((W // 2, 1340), str(n), "bold", 150, R.GOLD), t, t + 1.0, 0.2, 0.2)
    add(_plain((W // 2, 1010), "ENGLISH", "bold", 30, R.GOLD), 6.8)
    add(_text((W // 2, 1120), w["english"], "bold", 100, R.CREAM, 900), 6.8)
    add(_plain((W // 2, 1260), "URDU", "bold", 30, R.GOLD), 8.0)
    add(_text((W // 2, 1370), w["urdu"], "arabic", 120, R.CREAM, 900, True), 8.0)
    add(_plain((W // 2, 1480), f"Follow {handle} for a new word daily", "reg", 34, R.MUTED), 9.2)
    return E

def alpha_at(t, s, e, fi=0.5, fo=0.4):
    if t < s:
        return 0.0
    a = min(1.0, (t - s) / fi)
    if e is not None and t > e - fo:
        a = min(a, max(0.0, (e - t) / fo))
    return a

def render_cover(w, level, day, handle, path):
    """Reel cover (9:16). Content sits in the centre so the 3:4 profile-grid crop still shows it."""
    img = _bg()
    d = ImageDraw.Draw(img)
    d.text((W // 2, 520), "WORD OF THE DAY", font=R.font("bold", 48), fill=R.GOLD, anchor="mm")
    R.draw_fit(d, (W // 2, 860), w["arabic"], "arabic", 340, R.CREAM, 880, True)
    d.text((W // 2, 1120), w["transliteration"], font=R.font("reg", 60), fill=R.GOLD, anchor="mm")
    d.text((W // 2, 1300), "Do you know it?", font=R.font("bold", 56), fill=R.CREAM, anchor="mm")
    d.text((W // 2, 1400), handle, font=R.font("reg", 36), fill=R.MUTED, anchor="mm")
    img.save(path, "JPEG", quality=94)

# ---------- voice (free, via edge-tts; falls back to a silent Reel on any error) ----------
VOICES = {"ar": os.getenv("VOICE_AR", "ar-SA-HamedNeural"),
          "en": os.getenv("VOICE_EN", "en-US-GuyNeural"),
          "ur": os.getenv("VOICE_UR", "ur-PK-AsadNeural")}

def _speakable(text):
    text = re.sub(r"\(.*?\)", "", text)          # drop things like "(Zakat)"
    return re.sub(r"\s*/\s*", ", ", text).strip()  # "Peace / Hello" -> "Peace, Hello"

async def _tts(text, voice, rate, path):
    import edge_tts
    await edge_tts.Communicate(text, voice, rate=rate).save(path)

def make_voice_clips(w, tmp):
    """Returns [(mp3_path, delay_ms)] matching the on-screen timeline, or [] if voice is unavailable."""
    if os.getenv("REEL_VOICE", "1") == "0":
        return []
    plan = [("ar", w["arabic"], "-15%", 1000), ("en", _speakable(w["english"]), "+0%", 6900),
            ("ur", _speakable(w["urdu"]), "+0%", 8100), ("ar", w["arabic"], "-15%", 9700)]
    clips = []
    try:
        for i, (lang, text, rate, delay) in enumerate(plan):
            path = os.path.join(tmp, f"v{i}.mp3")
            asyncio.run(_tts(text, VOICES[lang], rate, path))
            clips.append((path, delay))
        return clips
    except Exception as e:
        print(f"WARNING: voice generation failed ({e}); posting a silent Reel.")
        return []

def mux_audio(video, clips, out_path):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", video]
    for path, _ in clips:
        cmd += ["-i", path]
    parts = [f"[{i+1}:a]aresample=44100,adelay={d}|{d}[a{i}]" for i, (_, d) in enumerate(clips)]
    mix = "".join(f"[a{i}]" for i in range(len(clips)))
    graph = ";".join(parts) + f";{mix}amix=inputs={len(clips)}:normalize=0,apad[aout]"
    cmd += ["-filter_complex", graph, "-map", "0:v", "-map", "[aout]", "-t", str(DUR),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out_path]
    subprocess.run(cmd, check=True)

def render_reel(w, level, day, handle, out_path):
    with tempfile.TemporaryDirectory() as tmp:
        silent = os.path.join(tmp, "silent.mp4")
        _render_silent(w, level, day, handle, silent)
        clips = make_voice_clips(w, tmp)
        if clips:
            try:
                mux_audio(silent, clips, out_path)
                return
            except Exception as e:
                print(f"WARNING: audio mixing failed ({e}); posting a silent Reel.")
        os.replace(silent, out_path) if os.path.exists(silent) else None

def _render_silent(w, level, day, handle, out_path):
    bg = _bg()
    elements = build_elements(w, level, day, handle)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-t", str(DUR), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-crf", "23", "-preset", "veryfast", "-c:a", "aac", "-b:a", "64k",
           "-movflags", "+faststart", out_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(int(DUR * FPS)):
        t = f / FPS
        frame = bg.copy()
        for layer, s, e, fi, fo in elements:
            a = alpha_at(t, s, e, fi, fo)
            if a <= 0:
                continue
            dy = int(30 * (1 - a))
            mask = layer.getchannel("A").point(lambda v, a=a: int(v * a))
            frame.paste(layer.convert("RGB"), (0, dy), mask)
        p.stdin.write(frame.tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg failed")
