import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import arabic_reshaper
from bidi.algorithm import get_display
from common import *
font_manager.fontManager.addfont(font())
plt.rcParams["font.family"] = "Noto Naskh Arabic"
labels = ["يناير", "فبراير", "مارس"]
def fix(s): return get_display(arabic_reshaper.reshape(s))
for mode in ["naive", "fixed"]:
    f = fix if mode == "fixed" else (lambda s: s)
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.bar([f(l) for l in labels], [10, 25, 18])
    ax.set_title(f(TEXT))
    ax.set_ylabel(f("الإيرادات (ألف)"))
    fig.tight_layout()
    fig.savefig(f"{OUT}/matplotlib_{mode}.png", dpi=110)
print("matplotlib", matplotlib.__version__)
# vector backends with native text (3.11+)
fig, ax = plt.subplots(figsize=(6, 1.2)); ax.axis("off")
ax.text(0.5, 0.5, TEXT, ha="center", va="center", fontsize=14)
fig.savefig(f"{OUT}/matplotlib_native.pdf"); fig.savefig(f"{OUT}/matplotlib_native.svg")
pdf_to_png(f"{OUT}/matplotlib_native.pdf", f"{OUT}/matplotlib_native_pdf.png")
