import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import arabic_reshaper
from bidi.algorithm import get_display

_rs = arabic_reshaper.ArabicReshaper(configuration={"delete_harakat": False})

def ar(t):
    # matplotlib 3.10 has no Arabic shaping/bidi: reshape + reorder manually
    return get_display(_rs.reshape(t))

plt.rcParams["font.family"] = "Noto Sans Arabic"

products = ["قهوة عربية", "تمر سكري", "عود كمبودي"]
values = [340, 280, 150]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
# largest at top
bars = ax.barh([ar(p) for p in products][::-1], values[::-1], color="#2a6f97", height=0.6)
ax.set_title(ar("أكثر المنتجات مبيعًا – أكتوبر"), fontsize=15, pad=12)
ax.set_xlabel(ar("عدد الطلبات"), fontsize=12)
# RTL layout: bars grow leftward, category labels on the right
ax.invert_xaxis()
ax.yaxis.tick_right()
ax.tick_params(axis="y", length=0, labelsize=12)
for b, v in zip(bars, values[::-1]):
    ax.text(b.get_width() + 5, b.get_y() + b.get_height()/2, str(v),
            va="center", ha="right", fontsize=11)
ax.set_xlim(max(values) * 1.12, 0)
for s in ("top", "left"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", alpha=0.3)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig("chart.png")
