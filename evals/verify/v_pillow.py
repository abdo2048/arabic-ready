from PIL import Image, ImageDraw, ImageFont, features
import PIL, arabic_reshaper
from bidi.algorithm import get_display
from common import *
fixed = get_display(arabic_reshaper.reshape(TEXT))
cases = [
  ("basic_naive", ImageFont.Layout.BASIC, TEXT, {}),
  ("basic_reshaped", ImageFont.Layout.BASIC, fixed, {}),
  ("raqm_native", ImageFont.Layout.RAQM, TEXT, {"direction": "rtl"}),
  ("raqm_plus_reshape_DOUBLE", ImageFont.Layout.RAQM, fixed, {}),
]
for name, layout, text, kw in cases:
    img = Image.new("RGB", (760, 90), "white")
    d = ImageDraw.Draw(img)
    fnt = ImageFont.truetype(font(), 34, layout_engine=layout)
    # right-align: anchor "ra" at the right edge
    d.text((740, 20), text, font=fnt, fill="black", anchor="ra", **kw)
    d.text((10, 2), name, font=ImageFont.truetype(font("DejaVuSans.ttf"), 12), fill="red")
    img.save(f"{OUT}/pillow_{name}.png")
print("Pillow", PIL.__version__, "raqm", features.check("raqm"), features.version("raqm"))
