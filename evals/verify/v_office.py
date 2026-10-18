import subprocess, docx, pptx
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pptx import Presentation
from pptx.util import Inches, Pt as PPt
from common import *

def to_png(path):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", OUT, path],
                   check=True, capture_output=True)
    pdf = os.path.splitext(path)[0] + ".pdf"
    pdf_to_png(pdf, os.path.splitext(path)[0] + ".png", zoom=1.2)

def set_rtl_paragraph(p):
    pPr = p._p.get_or_add_pPr()
    bidi = OxmlElement("w:bidi"); pPr.insert(0, bidi)

def set_rtl_run(run, font="Noto Naskh Arabic", size=14, bold=False):
    rPr = run._r.get_or_add_rPr()
    fonts = rPr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts"); rPr.insert(0, fonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs"):
        fonts.set(qn(a), font)
    if bold:
        rPr.append(OxmlElement("w:b")); rPr.append(OxmlElement("w:bCs"))
    for tag in ("w:sz", "w:szCs"):
        e = OxmlElement(tag); e.set(qn("w:val"), str(size * 2)); rPr.append(e)
    rtl = OxmlElement("w:rtl"); rPr.append(rtl)
    lang = OxmlElement("w:lang"); lang.set(qn("w:bidi"), "ar-SA"); rPr.append(lang)

# naive
d = Document()
d.add_heading("تقرير المبيعات", 1)
p = d.add_paragraph(); r = p.add_run(TEXT); r.font.size = Pt(14); r.bold = True
t = d.add_table(rows=2, cols=3); t.style = "Table Grid"
for i, v in enumerate(["المنتج", "الكمية", "السعر"]): t.cell(0, i).text = v
for i, v in enumerate(["قلم", "3", "12.50"]): t.cell(1, i).text = v
d.save(f"{OUT}/docx_naive.docx"); to_png(f"{OUT}/docx_naive.docx")

# fixed
d = Document()
# document defaults: rtl + cs font for every run (styles.xml rPrDefault)
rpr_default = d.styles.element.find(qn("w:docDefaults")).find(qn("w:rPrDefault")).find(qn("w:rPr"))
f = rpr_default.find(qn("w:rFonts"))
f.set(qn("w:cs"), "Noto Naskh Arabic")
h = d.add_heading(level=1); set_rtl_paragraph(h); set_rtl_run(h.add_run("تقرير المبيعات"), size=20, bold=True)
p = d.add_paragraph(); set_rtl_paragraph(p); set_rtl_run(p.add_run(TEXT), bold=True)
t = d.add_table(rows=2, cols=3); t.style = "Table Grid"
tblPr = t._tbl.tblPr; bv = OxmlElement("w:bidiVisual"); tblPr.append(bv)
for row, vals in enumerate([["المنتج", "الكمية", "السعر"], ["قلم", "3", "12.50"]]):
    for i, v in enumerate(vals):
        c = t.cell(row, i); c.text = ""
        cp = c.paragraphs[0]; set_rtl_paragraph(cp); set_rtl_run(cp.add_run(v), size=12)
d.save(f"{OUT}/docx_fixed.docx"); to_png(f"{OUT}/docx_fixed.docx")

# size gotcha: w:sz only (no w:szCs) and w:b only (no w:bCs)
d = Document(); p = d.add_paragraph(); set_rtl_paragraph(p)
r = p.add_run("حجم 28 بدون szCs"); r.font.size = Pt(28); r.bold = True
rPr = r._r.get_or_add_rPr(); rPr.append(OxmlElement("w:rtl"))
p = d.add_paragraph(); set_rtl_paragraph(p); set_rtl_run(p.add_run("حجم 28 مع szCs"), size=28, bold=True)
d.save(f"{OUT}/docx_szcs.docx"); to_png(f"{OUT}/docx_szcs.docx")

# pptx
for mode in ["naive", "fixed"]:
    prs = Presentation(); prs.slide_width, prs.slide_height = Inches(10), Inches(3)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    tb = s.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(2.4)); tf = tb.text_frame; tf.word_wrap = True
    for i, line in enumerate(["نتائج الربع الثالث", TEXT, "• نمو 25% مقارنة بالعام الماضي"]):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        run = para.add_run(); run.text = line; run.font.size = PPt(28 if i == 0 else 20)
        if mode == "fixed":
            pPr = para._p.get_or_add_pPr(); pPr.set("rtl", "1"); pPr.set("algn", "r")
            rPr = run._r.get_or_add_rPr(); rPr.set("lang", "ar-SA")
            cs = OxmlElement("a:cs"); cs.set("typeface", "Noto Naskh Arabic"); rPr.append(cs)
            la = OxmlElement("a:latin"); la.set("typeface", "Noto Naskh Arabic"); rPr.insert(0, la)
    prs.save(f"{OUT}/pptx_{mode}.pptx"); to_png(f"{OUT}/pptx_{mode}.pptx")
print("python-docx", docx.__version__, "python-pptx", pptx.__version__)
print(subprocess.run(["soffice", "--version"], capture_output=True, text=True).stdout.strip())
