from PIL import Image, ImageDraw, ImageFont, features

W = H = 1080
BOLD = "/root/.fonts/Cairo-700.ttf"
REG = "/root/.fonts/Cairo-400.ttf"
assert features.check("raqm"), "Pillow needs libraqm for correct Arabic shaping"

# Vertical gradient background
img = Image.new("RGB", (W, H))
top, bot = (190, 24, 60), (90, 16, 80)
d = ImageDraw.Draw(img)
for y in range(H):
    t = y / (H - 1)
    d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bot)))

# Decorative circles
over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
od = ImageDraw.Draw(over)
od.ellipse((-220, -220, 380, 380), fill=(255, 255, 255, 28))
od.ellipse((760, 760, 1300, 1300), fill=(255, 255, 255, 22))
img = Image.alpha_composite(img.convert("RGBA"), over)
d = ImageDraw.Draw(img)

def text_fit(s, path, max_size, max_w):
    size = max_size
    while size > 20:
        f = ImageFont.truetype(path, size)
        l, t, r, b = d.textbbox((0, 0), s, font=f, direction="rtl", language="ar")
        if r - l <= max_w:
            return f
        size -= 4
    return f

def center(s, font, y, fill, rtl=True):
    kw = dict(direction="rtl", language="ar") if rtl else {}
    d.text((W / 2, y), s, font=font, fill=fill, anchor="mm", **kw)

margin = 90
line1, line2 = "خصم 30%", "على جميع المنتجات"
f1 = text_fit(line1, BOLD, 220, W - 2 * margin)
f2 = text_fit(line2, BOLD, 110, W - 2 * margin)
center(line1, f1, 350, (255, 255, 255))
center(line2, f2, 575, (255, 255, 255))

# Badge with "لفترة محدودة!"
fb = ImageFont.truetype(BOLD, 64)
sub = "لفترة محدودة!"
l, t, r, b = d.textbbox((W / 2, 720), sub, font=fb, anchor="mm", direction="rtl", language="ar")
d.rounded_rectangle((l - 50, t - 26, r + 50, b + 26), radius=50, fill=(255, 210, 63))
center(sub, fb, 720, (90, 16, 80))

# URL (LTR)
fu = ImageFont.truetype(REG, 48)
center("shop.example.com", fu, 900, (255, 255, 255, 230), rtl=False)

img.convert("RGB").save("post.png")
print("saved post.png")
