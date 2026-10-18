import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

plt.rcParams["font.family"] = "IBM Plex Sans Arabic"
plt.rcParams["text.language"] = "ar"   # matplotlib 3.11+ shapes Arabic natively: raw strings

months = ["يناير", "فبراير", "مارس"]
sales = [120, 180, 150]

fig, ax = plt.subplots(figsize=(8, 5.5))
bars = ax.bar(months, sales, color="#2E7D6B", width=0.55, label="المبيعات (ألف ريال)")
ax.bar_label(bars, padding=4, fontsize=12)

# Months are a time axis: keep chronological order left to right; value axis on the right.
ax.yaxis.tick_right(); ax.yaxis.set_label_position("right")
ax.set_title("مبيعات الربع الأول", fontsize=17, fontweight="bold", pad=14)
ax.set_xlabel("الشهر", fontsize=13)
ax.set_ylabel("المبيعات (ألف ريال)", fontsize=13)
ax.set_ylim(0, 210)
ax.tick_params(axis="x", labelsize=13)
ax.grid(axis="y", alpha=0.3); ax.set_axisbelow(True)
for s in ("top", "left"):
    ax.spines[s].set_visible(False)
ax.legend(loc="upper right", markerfirst=False, frameon=False, fontsize=12)

fig.tight_layout()
fig.savefig("chart.png", dpi=150)
