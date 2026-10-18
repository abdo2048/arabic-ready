import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# matplotlib >= 3.11 shapes Arabic text and applies bidi natively (no reshaper needed)
plt.rcParams["font.family"] = "Noto Kufi Arabic"
plt.rcParams["axes.unicode_minus"] = False

months = ["يناير", "فبراير", "مارس"]
sales = [120, 180, 150]

fig, ax = plt.subplots(figsize=(8, 5.5), dpi=150)
bars = ax.bar(months, sales, color="#2a78b8", width=0.55, label="المبيعات (ألف ريال)")
ax.bar_label(bars, labels=[str(v) for v in sales], padding=4, fontsize=12)

ax.set_title("مبيعات الربع الأول", fontsize=16, pad=14)
ax.set_xlabel("الشهر", fontsize=13)
ax.set_ylabel("المبيعات (بالألف ريال)", fontsize=13)
ax.set_ylim(0, 210)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", alpha=0.3)
ax.set_axisbelow(True)
ax.legend(loc="upper right", fontsize=11, frameon=False, markerfirst=False)

fig.tight_layout()
fig.savefig("chart.png")
