import os, urllib.request
from PIL import Image, ImageDraw, ImageFont, features
import arabic_reshaper
from bidi.algorithm import get_display

W, H = 1080, 1350
BG1, BG2 = (10, 46, 42), (4, 22, 24)
GOLD, CREAM, MUTED = (226, 184, 96), (248, 243, 230), (150, 178, 170)

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
FONTS = {
    "arabic": ("NotoNaskhArabic.ttf", BASE + "notonaskharabic/NotoNaskhArabic%5Bwght%5D.ttf"),
    "bold": ("Poppins-SemiBold.ttf", BASE + "poppins/Poppins-SemiBold.ttf"),
    "reg": ("Poppins-Regular.ttf", BASE + "poppins/Poppins-Regular.ttf"),
}
RAQM = features.check("raqm")

def font(kind, size):
    name, url = FONTS[kind]
    path = os.path.join(FONT_DIR, name)
    if not os.path.exists(path):
        os.makedirs(FONT_DIR, exist_ok=True)
        urllib.request.urlretrieve(url, path)
    return ImageFont.truetype(path, size)

def rtl(text):
    """Prepare Arabic/Urdu text for Pillow (RAQM shapes natively; otherwise reshape manually)."""
    return text if RAQM else get_display(arabic_reshaper.reshape(text))

def background():
    img = Image.new("RGB", (W, H), BG1)
    px = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        px.line([(0, y), (W, y)], fill=tuple(int(BG1[i] + (BG2[i] - BG1[i]) * t) for i in range(3)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((40, 40, W - 40, H - 40), 36, outline=GOLD, width=3)
    return img, d

def draw_fit(d, xy, text, kind, size, fill, max_w, is_rtl=False):
    while size > 20:
        f = font(kind, size)
        kw = {"direction": "rtl", "language": "ar"} if (is_rtl and RAQM) else {}
        s = rtl(text) if is_rtl else text
        if d.textlength(s, font=f, **kw) <= max_w:
            break
        size -= 4
    d.text(xy, s, font=f, fill=fill, anchor="mm", **kw)

def footer(d, handle):
    d.text((W // 2, H - 90), handle, font=font("reg", 30), fill=MUTED, anchor="mm")

def slide_cover(w, level, day, handle, path):
    img, d = background()
    d.text((W // 2, 150), "WORD OF THE DAY", font=font("bold", 40), fill=GOLD, anchor="mm")
    d.text((W // 2, 215), f"Day {day}  •  {level}", font=font("reg", 32), fill=MUTED, anchor="mm")
    draw_fit(d, (W // 2, 560), w["arabic"], "arabic", 300, CREAM, 880, True)
    d.text((W // 2, 800), w["transliteration"], font=font("reg", 52), fill=GOLD, anchor="mm")
    d.text((W // 2, 1010), "Do you know what it means?", font=font("bold", 46), fill=CREAM, anchor="mm")
    d.text((W // 2, 1085), "Swipe to check   >>", font=font("reg", 36), fill=MUTED, anchor="mm")
    footer(d, handle)
    img.save(path, "JPEG", quality=94)

def slide_meaning(w, handle, path):
    img, d = background()
    draw_fit(d, (W // 2, 230), w["arabic"], "arabic", 170, GOLD, 800, True)
    d.text((W // 2, 360), w["transliteration"], font=font("reg", 40), fill=MUTED, anchor="mm")
    d.line([(240, 440), (W - 240, 440)], fill=GOLD, width=2)
    d.text((W // 2, 530), "ENGLISH", font=font("bold", 30), fill=GOLD, anchor="mm")
    draw_fit(d, (W // 2, 650), w["english"], "bold", 100, CREAM, 880)
    d.line([(240, 780), (W - 240, 780)], fill=GOLD, width=2)
    d.text((W // 2, 870), "URDU", font=font("bold", 30), fill=GOLD, anchor="mm")
    draw_fit(d, (W // 2, 1030), w["urdu"], "arabic", 130, CREAM, 880, True)
    footer(d, handle)
    img.save(path, "JPEG", quality=94)

def slide_cta(handle, path):
    img, d = background()
    d.text((W // 2, 420), "Learn one Arabic word", font=font("bold", 58), fill=CREAM, anchor="mm")
    d.text((W // 2, 500), "every single day", font=font("bold", 58), fill=GOLD, anchor="mm")
    lines = ["Save this post", "Share with a friend", "Follow for tomorrow's word"]
    for i, t in enumerate(lines):
        y = 700 + i * 110
        d.rounded_rectangle((170, y - 42, W - 170, y + 42), 42, outline=GOLD, width=3)
        d.text((W // 2, y), t, font=font("reg", 40), fill=CREAM, anchor="mm")
    d.text((W // 2, 1120), handle, font=font("bold", 44), fill=GOLD, anchor="mm")
    img.save(path, "JPEG", quality=94)

def render_post(w, level, day, handle, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    paths = [os.path.join(out_dir, f"slide_{i}.jpg") for i in (1, 2, 3)]
    slide_cover(w, level, day, handle, paths[0])
    slide_meaning(w, handle, paths[1])
    slide_cta(handle, paths[2])
    return paths
