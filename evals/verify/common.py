import os, glob
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
TEXT = "فاتورة رقم 1024 للعميل Acme، الإجمالي 49.99 دولار؟"
SHORT = "المبيعات الشهرية"
def font(name="NotoNaskhArabic-400.ttf"):
    for d in [os.path.expanduser("~/.fonts"), "/usr/share/fonts"]:
        hits = glob.glob(os.path.join(d, "**", name), recursive=True)
        if hits:
            return hits[0]
    raise FileNotFoundError(name)
def pdf_to_png(pdf, png, zoom=2):
    import pymupdf as fitz
    doc = fitz.open(pdf)
    doc[0].get_pixmap(matrix=fitz.Matrix(zoom, zoom)).save(png)
