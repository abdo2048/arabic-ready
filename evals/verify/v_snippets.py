"""Runs the snippets from references/documents.md and charts-images.md as written
(only font paths substituted) and renders each result to PNG."""
import os, re, subprocess, sys
from common import *
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "arabic-ready", "scripts"))
REF = os.path.join(HERE, "..", "..", "skills", "arabic-ready", "references")
NASKH = font("NotoNaskhArabic-400.ttf"); PLEX = font("IBMPlexSansArabic-400.ttf")

def blocks(md, lang):
    return re.findall(r"```" + lang + r"\n(.*?)```", open(os.path.join(REF, md), encoding="utf-8").read(), re.S)

def run_block(code, extra=None, cwd=OUT):
    code = (code.replace("NotoNaskhArabic-Regular.ttf", NASKH)
                .replace("IBMPlexSansArabic-Regular.ttf", PLEX)
                .replace('"/path/to/font/folder"', repr(os.path.dirname(NASKH)))
                .replace("<skill-dir>/scripts", os.path.join(HERE, "..", "..", "skills", "arabic-ready", "scripts")))
    g = {"__name__": "__snippet__"}
    if extra: g.update(extra)
    old = os.getcwd(); os.chdir(cwd)
    try:
        exec(compile(code, "<snippet>", "exec"), g)
    finally:
        os.chdir(old)
    return g

def office_png(name):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", OUT, os.path.join(OUT, name)], capture_output=True, check=True)
    pdf_to_png(os.path.join(OUT, os.path.splitext(name)[0] + ".pdf"), os.path.join(OUT, "snippet_" + os.path.splitext(name)[0] + ".png"), 1.2)

py_docs = blocks("documents.md", "python")
# 0: make_rtl_document ... saves report.docx
run_block(py_docs[0]); office_png("report.docx")
# 1: python-pptx -> deck.pptx
run_block(py_docs[1]); office_png("deck.pptx")
# 2: playwright, 3: weasyprint (needs `html` from 2)
g = run_block(py_docs[2]); pdf_to_png(os.path.join(OUT, "invoice.pdf"), os.path.join(OUT, "snippet_playwright_invoice.png"), 1)
run_block(py_docs[3], {"html": g["html"]}); pdf_to_png(os.path.join(OUT, "invoice.pdf"), os.path.join(OUT, "snippet_weasy_invoice.png"), 1)
LONG = "هذا نص عربي طويل لاختبار التفاف الأسطر عندما يكون النص أطول من عرض الصفحة المتاح، والسطر الأول يجب أن يظهر في الأعلى دائما."
# 4: fpdf2
run_block(py_docs[4], {"long_arabic_text": LONG}); pdf_to_png(os.path.join(OUT, "invoice.pdf"), os.path.join(OUT, "snippet_fpdf2.png"), 1)
# 5: reportlab canvas, 6: reportlab wrap (uses prepare + Naskh registration from 5)
g = run_block(py_docs[5]); pdf_to_png(os.path.join(OUT, "out.pdf"), os.path.join(OUT, "snippet_reportlab_canvas.png"), 1)
from reportlab.platypus import SimpleDocTemplate
p = os.path.join(OUT, "snippet_reportlab_wrap.pdf")
doc = SimpleDocTemplate(p, pagesize=(340, 200), leftMargin=20, rightMargin=20, topMargin=10, bottomMargin=10)
g = run_block(py_docs[6], {"long_text": LONG, "doc": doc, "prepare": g["prepare"]})
doc.build(g["story"])
pdf_to_png(p, p[:-4] + ".png", 1.5)
# 7: PyMuPDF
run_block(py_docs[7]); pdf_to_png(os.path.join(OUT, "out.pdf"), os.path.join(OUT, "snippet_pymupdf.png"), 1)

py_charts = blocks("charts-images.md", "python")
# 0: prepare() usage with ax -> needs ax
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(4, 1.5)); run_block(py_charts[0], {"ax": ax})
# 1: basic matplotlib chart -> chart.png
run_block(py_charts[1]); os.replace(os.path.join(OUT, "chart.png"), os.path.join(OUT, "snippet_matplotlib.png"))
# 2: RTL layout block (needs ax from previous)
fig, ax = plt.subplots(figsize=(5, 3)); ax.bar(["أ", "ب", "ج"], [1, 3, 2], label="المبيعات")
run_block(py_charts[2], {"ax": ax}); fig.savefig(os.path.join(OUT, "snippet_matplotlib_layout.png"), dpi=90)
# 3+4: Pillow draw + wrap, both branches
for forced_basic in (False, True):
    from PIL import features
    orig = features.check
    if forced_basic: features.check = lambda name: False if name == "raqm" else orig(name)
    try:
        g = run_block(py_charts[3])
        if not forced_basic:
            from PIL import Image, ImageDraw
            img2 = Image.new("RGB", (1080, 600), "white")
            run_block(py_charts[4], {"d": ImageDraw.Draw(img2), "text": " ".join([g["text"]] * 3), "font": g["font"]})
            img2.save(os.path.join(OUT, "snippet_pillow_wrap.png"))
        g["img"].save(os.path.join(OUT, f"snippet_pillow_{'basic' if forced_basic else 'raqm'}.png"))
    finally:
        features.check = orig

# SVG + canvas from charts-images.md in Chromium
svg = [b for b in blocks("charts-images.md", "svg") if "<svg" in b][0]
js = blocks("charts-images.md", "js")[0]
html = f"""<!doctype html><html lang=ar dir=rtl><meta charset=utf-8><style>@font-face{{font-family:'IBM Plex Sans Arabic';src:url(file://{PLEX})}}
svg,canvas{{border:1px solid #ccc;display:block}}</style>{svg}<canvas id=c width=400 height=60></canvas>
<script type=module>const canvas=document.getElementById('c'); {js} document.title='done'</script></html>"""
open(os.path.join(OUT, "snippet_svg_canvas.html"), "w").write(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    pg = p.chromium.launch().new_page(viewport={"width": 420, "height": 150})
    pg.goto("file://" + os.path.join(OUT, "snippet_svg_canvas.html")); pg.wait_for_function("document.title=='done'")
    pg.screenshot(path=os.path.join(OUT, "snippet_svg_canvas.png"))
print("all snippets ran")
