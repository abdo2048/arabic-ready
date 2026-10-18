import arabic_reshaper, reportlab, fpdf, fitz, weasyprint
from bidi.algorithm import get_display
from common import *
fixed = get_display(arabic_reshaper.reshape(TEXT))
F = font(); FB = font("NotoNaskhArabic-700.ttf")

# --- reportlab
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont("Naskh", F))
for mode, t in [("naive", TEXT), ("reshaped", fixed)]:
    p = f"{OUT}/reportlab_{mode}.pdf"
    c = canvas.Canvas(p, pagesize=(420, 80)); c.setFont("Naskh", 16)
    c.drawRightString(410, 35, t); c.save(); pdf_to_png(p, p[:-4] + ".png")

# reportlab Paragraph (platypus) with reshaped text, right aligned
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
p = f"{OUT}/reportlab_paragraph.pdf"
st = ParagraphStyle("ar", fontName="Naskh", fontSize=14, leading=24, alignment=TA_RIGHT)
SimpleDocTemplate(p, pagesize=(420, 160), leftMargin=10, rightMargin=10, topMargin=10, bottomMargin=10).build(
    [Paragraph(get_display(arabic_reshaper.reshape(TEXT)), st)])
pdf_to_png(p, p[:-4] + ".png")

# --- fpdf2
from fpdf import FPDF
for mode in ["naive", "shaping"]:
    pdf = FPDF(format=(150, 30)); pdf.set_margins(5, 5, 5); pdf.set_auto_page_break(False); pdf.add_page()
    pdf.add_font("Naskh", "", F); pdf.set_font("Naskh", size=14)
    if mode == "shaping":
        pdf.set_text_shaping(use_shaping_engine=True, direction="rtl", script="arab", language="ar")
    pdf.cell(w=0, h=12, text=TEXT, align="R")
    p = f"{OUT}/fpdf2_{mode}.pdf"; pdf.output(p); pdf_to_png(p, p[:-4] + ".png")

# --- PyMuPDF
for mode in ["insert_text", "insert_htmlbox"]:
    doc = fitz.open(); page = doc.new_page(width=420, height=80)
    if mode == "insert_text":
        page.insert_text((10, 45), TEXT, fontfile=F, fontname="naskh", fontsize=16)
    else:
        page.insert_htmlbox(fitz.Rect(10, 10, 410, 70),
            f'<p dir="rtl" style="font-size:16px">{TEXT}</p>',
            archive=fitz.Archive(os.path.dirname(F)),
            css=f'@font-face {{font-family: naskh; src: url({os.path.basename(F)});}} p {{font-family: naskh;}}')
    p = f"{OUT}/pymupdf_{mode}.pdf"; doc.save(p); pdf_to_png(p, p[:-4] + ".png")

# --- WeasyPrint
html = f'''<html dir="rtl" lang="ar"><style>@page {{size: 420px 80px; margin: 10px}}
@font-face {{font-family: Naskh; src: url(file://{F})}} body {{font-family: Naskh; font-size: 16px}}</style>
<body><p>{TEXT}</p></body></html>'''
p = f"{OUT}/weasyprint.pdf"; weasyprint.HTML(string=html).write_pdf(p); pdf_to_png(p, p[:-4] + ".png")
import uharfbuzz
print("reportlab", reportlab.Version, "fpdf2", fpdf.__version__, "pymupdf", fitz.VersionBind,
      "weasyprint", weasyprint.__version__, "uharfbuzz", uharfbuzz.__version__)

# reportlab multi-line paragraph: reshaped+bidi text wrapped by reportlab
LONG = "هذا نص عربي طويل لاختبار التفاف الأسطر في مكتبة ريبورت لاب عندما يكون النص أطول من عرض الصفحة المتاح، السطر الأول يجب أن يظهر في الأعلى."
p = f"{OUT}/reportlab_multiline_wrong.pdf"
SimpleDocTemplate(p, pagesize=(300, 140), leftMargin=10, rightMargin=10, topMargin=10, bottomMargin=10).build(
    [Paragraph(get_display(arabic_reshaper.reshape(LONG)), st)])
pdf_to_png(p, p[:-4] + ".png")
# fix: wrap logical text first, then reshape+bidi each line
from reportlab.pdfbase.pdfmetrics import stringWidth
def wrap_rtl(text, fontname, size, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if stringWidth(get_display(arabic_reshaper.reshape(t)), fontname, size) <= width: cur = t
        else: lines.append(cur); cur = w
    return lines + [cur]
p = f"{OUT}/reportlab_multiline_fixed.pdf"
SimpleDocTemplate(p, pagesize=(300, 140), leftMargin=10, rightMargin=10, topMargin=10, bottomMargin=10).build(
    [Paragraph(get_display(arabic_reshaper.reshape(l)), st) for l in wrap_rtl(LONG, "Naskh", 14, 280)])
pdf_to_png(p, p[:-4] + ".png")
# fpdf2 multi_cell with shaping
pdf = FPDF(format=(110, 50)); pdf.set_margins(5, 5, 5); pdf.set_auto_page_break(False); pdf.add_page()
pdf.add_font("Naskh", "", F); pdf.set_font("Naskh", size=12)
pdf.set_text_shaping(use_shaping_engine=True, direction="rtl", script="arab", language="ar")
pdf.multi_cell(w=0, h=8, text=LONG, align="R")
p = f"{OUT}/fpdf2_multicell.pdf"; pdf.output(p); pdf_to_png(p, p[:-4] + ".png")
