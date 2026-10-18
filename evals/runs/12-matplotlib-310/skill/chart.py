import importlib.util  # noqa: F401  (shape_text.capabilities() needs it loaded)
import sys
sys.path.insert(0, "/home/user/Rtl-arabic/skills/arabic-ready/scripts")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from shape_text import prepare

# matplotlib 3.10 does not shape Arabic: every string goes through prepare()
A = lambda s: prepare(s, target="matplotlib")

font_manager.fontManager.addfont("/root/.fonts/IBMPlexSansArabic-400.ttf")
font_manager.fontManager.addfont("/root/.fonts/IBMPlexSansArabic-700.ttf")
plt.rcParams["font.family"] = "IBM Plex Sans Arabic"

products = ["قهوة عربية", "تمر سكري", "عود كمبودي"]
orders = [340, 280, 150]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
y = range(len(products))
bars = ax.barh(y, orders, color="#2a6f97", height=0.6)
ax.set_yticks(list(y), [A(p) for p in products], fontsize=12)
ax.invert_yaxis()                 # best seller on top
ax.invert_xaxis()                 # RTL: bars grow leftwards
ax.yaxis.tick_right()             # labels on the right
ax.tick_params(axis="y", length=0)
for b, v in zip(bars, orders):
    ax.text(b.get_width() + 5, b.get_y() + b.get_height() / 2, str(v),
            va="center", ha="right", fontsize=11)
ax.set_xlim(max(orders) * 1.15, 0)
ax.set_xlabel(A("عدد الطلبات"), fontsize=12)
ax.set_title(A("أكثر المنتجات مبيعًا – أكتوبر"), fontsize=15, fontweight="bold", loc="right")
for s in ("top", "left"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", alpha=0.3)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig("chart.png")
