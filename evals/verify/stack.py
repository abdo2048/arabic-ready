import sys
from PIL import Image, ImageDraw, ImageFont
out, *files = sys.argv[1:]
ims = [Image.open(f).convert("RGB") for f in files]
W = max(i.width for i in ims); H = sum(i.height + 18 for i in ims)
c = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(c); y = 0
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
for p, i in zip(files, ims):
    d.text((4, y + 2), p.split("/")[-1], fill="red", font=f); c.paste(i, (0, y + 18)); y += i.height + 18
c.save(out)
