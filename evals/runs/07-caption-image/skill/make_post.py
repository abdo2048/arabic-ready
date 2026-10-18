"""Instagram post 1080x1080 with Arabic text, drawn with Pillow (raqm layout)."""
import sys
from PIL import Image, ImageDraw, ImageFont, features

W = H = 1080
PAD = int(W * 0.08)
BOLD = "/root/.fonts/Cairo-700.ttf"
REG = "/root/.fonts/Cairo-400.ttf"

TITLE = "خصم 30% على جميع المنتجات"
SUB = "لفترة محدودة!"
URL = "shop.example.com"

RAQM = features.check("raqm")
if not RAQM:  # fallback: shape manually for glyph-by-glyph rendering
    sys.path.insert(0, "/home/user/Rtl-arabic/skills/arabic-ready/scripts")
    from shape_text import prepare
LAYOUT = ImageFont.Layout.RAQM if RAQM else ImageFont.Layout.BASIC

def font(path, size):
    return ImageFont.truetype(path, size, layout_engine=LAYOUT)

def ar_kwargs():
    return {"direction": "rtl", "language": "ar"} if RAQM else {}

def show(t):
    return t if RAQM else prepare(t, force=True)

def wrap_rtl(d, text, f, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if d.textlength(show(trial), font=f, **ar_kwargs()) <= max_w:
            cur = trial
        else:
            lines.append(cur); cur = word
    return lines + [cur]

# Background: vertical gradient
img = Image.new("RGB", (W, H))
top, bot = (124, 31, 74), (230, 81, 60)
px = img.load()
for y in range(H):
    t = y / (H - 1)
    c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
    for x in range(W):
        px[x, y] = c
d = ImageDraw.Draw(img)

# Decorative frame
d.rounded_rectangle((40, 40, W - 40, H - 40), radius=48, outline=(255, 255, 255), width=4)

cx = W // 2
title_f = font(BOLD, 128)
sub_f = font(BOLD, 72)
url_f = font(REG, 46)

title_lines = wrap_rtl(d, TITLE, title_f, W - 2 * PAD)
title_lh = int(title_f.size * 1.6)
sub_lh = int(sub_f.size * 1.7)
url_box_h = 100
gap1, gap2 = 30, 70
total = len(title_lines) * title_lh + gap1 + sub_lh + gap2 + url_box_h
y = (H - total) // 2

for line in title_lines:
    d.text((cx, y + title_lh // 2), show(line), font=title_f, fill="white", anchor="mm", **ar_kwargs())
    y += title_lh
y += gap1
d.text((cx, y + sub_lh // 2), show(SUB), font=sub_f, fill=(255, 224, 130), anchor="mm", **ar_kwargs())
y += sub_lh + gap2

# URL on its own line, LTR, in a pill
uw = d.textlength(URL, font=url_f, direction="ltr") if RAQM else d.textlength(URL, font=url_f)
bw = int(uw + 90)
d.rounded_rectangle((cx - bw // 2, y, cx + bw // 2, y + url_box_h), radius=url_box_h // 2, fill="white")
kw = {"direction": "ltr", "language": "en"} if RAQM else {}
d.text((cx, y + url_box_h // 2), URL, font=url_f, fill=top, anchor="mm", **kw)

img.save("post.png")
print("saved post.png, raqm =", RAQM, "title lines =", title_lines)
