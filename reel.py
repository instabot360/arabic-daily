"""Render a 9.5s vertical Reel (1080x1920) for one word using Pillow + ffmpeg."""
import subprocess
from PIL import Image, ImageDraw
import render as R

W, H, FPS, DUR = 1080, 1920, 24, 9.5

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
    """(layer, start, end_or_None) ; fades in over 0.5s, fades out over 0.4s at end."""
    E = []
    add = lambda fn, s, e=None: E.append((_layer(fn), s, e))
    add(_plain((W // 2, 330), "WORD OF THE DAY", "bold", 44, R.GOLD), 0.0)
    add(_plain((W // 2, 395), f"Day {day}  •  {level}", "reg", 32, R.MUTED), 0.2)
    add(_text((W // 2, 640), w["arabic"], "arabic", 300, R.CREAM, 880, True), 0.5)
    add(_plain((W // 2, 880), w["transliteration"], "reg", 56, R.GOLD), 1.3)
    add(_plain((W // 2, 1200), "What does it mean?", "bold", 54, R.CREAM), 2.6, 5.4)
    for i, (n, t) in enumerate(((3, 3.4), (2, 4.1), (1, 4.8))):
        add(_plain((W // 2, 1330), str(n), "bold", 150, R.GOLD), t, t + 0.7)
    add(_plain((W // 2, 1010), "ENGLISH", "bold", 30, R.GOLD), 5.6)
    add(_text((W // 2, 1120), w["english"], "bold", 100, R.CREAM, 900), 5.6)
    add(_plain((W // 2, 1260), "URDU", "bold", 30, R.GOLD), 6.6)
    add(_text((W // 2, 1370), w["urdu"], "arabic", 120, R.CREAM, 900, True), 6.6)
    add(_plain((W // 2, 1480), f"Follow {handle} for a new word daily", "reg", 34, R.MUTED), 7.8)
    return E

def alpha_at(t, s, e):
    if t < s:
        return 0.0
    a = min(1.0, (t - s) / 0.5)
    if e is not None and t > e - 0.4:
        a = min(a, max(0.0, (e - t) / 0.4))
    return a

def render_reel(w, level, day, handle, out_path):
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
        for layer, s, e in elements:
            a = alpha_at(t, s, e)
            if a <= 0:
                continue
            dy = int(30 * (1 - a))
            mask = layer.getchannel("A").point(lambda v, a=a: int(v * a))
            frame.paste(layer.convert("RGB"), (0, dy), mask)
        p.stdin.write(frame.tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg failed")
