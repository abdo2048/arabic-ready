import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter
from PIL import Image, ImageDraw, ImageFont
from common import *

# --- matplotlib 3.11: legend, annotations, Arabic-Indic ticks, RTL category order
font_manager.fontManager.addfont(font("IBMPlexSansArabic-400.ttf"))
plt.rcParams["font.family"] = "IBM Plex Sans Arabic"
plt.rcParams["text.language"] = "ar"
AR = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
fig, ax = plt.subplots(figsize=(6.4, 3.6))
months = ["يناير", "فبراير", "مارس", "أبريل"]
ax.bar(months, [120, 180, 150, 210], label="المبيعات (ألف ريال)", color="#2f6f9f")
ax.plot(months, [100, 140, 160, 190], color="#d9822b", marker="o", label="المستهدف")
ax.invert_xaxis()                      # first category on the right
ax.yaxis.tick_right(); ax.yaxis.set_label_position("right")
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}".translate(AR)))
ax.set_title("المبيعات الشهرية ٢٠٢٦ — فرع الرياض")
ax.annotate("أعلى شهر!", xy=(3, 210), xytext=(2.4, 228), arrowprops=dict(arrowstyle="->"))
ax.set_ylim(0, 260)
ax.legend(loc="upper left")
fig.tight_layout(); fig.savefig(f"{OUT}/matplotlib_rtl_chart.png", dpi=110)

# --- Pillow + raqm: multiline, right aligned, wrapping by measured width
fnt = ImageFont.truetype(font("NotoNaskhArabic-400.ttf"), 30, layout_engine=ImageFont.Layout.RAQM)
caption = "عرض خاص لفترة محدودة: خصم 25% على جميع المنتجات حتى نهاية الشهر. اطلب الآن عبر shop.example.com"
img = Image.new("RGB", (620, 260), "#fff8ec"); d = ImageDraw.Draw(img)
def wrap(text, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt, direction="rtl", language="ar") <= width: cur = t
        else: lines.append(cur); cur = w
    return lines + [cur]
y = 20
for line in wrap(caption, 580):
    d.text((600, y), line, font=fnt, fill="#222", anchor="ra", direction="rtl", language="ar")
    y += 52
d.multiline_text((600, y + 4), "سطر أول\nسطر ثانٍ أطول قليلاً", font=fnt, fill="#a33", anchor="ra",
                 align="right", direction="rtl", language="ar", spacing=14)
img.save(f"{OUT}/pillow_caption_raqm.png")
