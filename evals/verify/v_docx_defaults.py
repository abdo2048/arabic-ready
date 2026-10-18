# python-docx: set RTL once in docDefaults; headings, lists, tables, header inherit it
import subprocess
from docx import Document
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from common import *

def make_rtl_document(font="Noto Naskh Arabic", size_pt=12, lang="ar-SA"):
    doc = Document()
    defaults = doc.styles.element.find(qn("w:docDefaults"))
    rpr = defaults.find(qn("w:rPrDefault")).find(qn("w:rPr"))
    fonts = rpr.find(qn("w:rFonts"))
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        fonts.set(qn(attr), font)
    for theme_attr in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        fonts.attrib.pop(qn(theme_attr), None)
    for tag in ("w:sz", "w:szCs"):
        el = rpr.find(qn(tag))
        if el is None:
            el = OxmlElement(tag); rpr.append(el)
        el.set(qn("w:val"), str(size_pt * 2))
    lang_el = rpr.find(qn("w:lang"))
    if lang_el is None:
        lang_el = OxmlElement("w:lang"); rpr.append(lang_el)
    lang_el.set(qn("w:bidi"), lang)
    rpr.append(OxmlElement("w:rtl"))
    ppr_default = defaults.find(qn("w:pPrDefault"))
    if ppr_default is None:
        ppr_default = OxmlElement("w:pPrDefault"); defaults.append(ppr_default)
    ppr = ppr_default.find(qn("w:pPr"))
    if ppr is None:
        ppr = OxmlElement("w:pPr"); ppr_default.append(ppr)
    ppr.insert(0, OxmlElement("w:bidi"))
    # heading styles carry their own theme fonts: point their complex-script font at ours
    for st in doc.styles:
        el = st.element.find(qn("w:rPr"))
        if el is not None and el.find(qn("w:rFonts")) is not None:
            f = el.find(qn("w:rFonts"))
            for theme_attr in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
                f.attrib.pop(qn(theme_attr), None)
            f.set(qn("w:cs"), font); f.set(qn("w:ascii"), font); f.set(qn("w:hAnsi"), font)
    return doc

def bold(run):
    run.bold = True
    run._r.get_or_add_rPr().append(OxmlElement("w:bCs"))

doc = make_rtl_document()
doc.sections[0].header.paragraphs[0].text = "شركة النور للتجارة — تقرير داخلي"
doc.add_heading("تقرير المبيعات الربعي", level=1)
p = doc.add_paragraph("ارتفعت المبيعات بنسبة 25% مقارنة بالربع السابق، وبلغ الإجمالي 1,250,000 ريال.")
bold(p.add_run(" نتيجة ممتازة."))
doc.add_heading("أبرز النقاط", level=2)
for t in ["افتتاح فرعين جديدين في الرياض وجدة", "إطلاق تطبيق الجوال (iOS وAndroid)", "خفض التكاليف 8%"]:
    doc.add_paragraph(t, style="List Bullet")
for t in ["المرحلة الأولى", "المرحلة الثانية"]:
    doc.add_paragraph(t, style="List Number")
tbl = doc.add_table(rows=3, cols=3); tbl.style = "Table Grid"
tbl._tbl.tblPr.append(OxmlElement("w:bidiVisual"))
for r, row in enumerate([["المنطقة", "المبيعات", "النمو"], ["الرياض", "520,000", "+12%"], ["جدة", "410,000", "+9%"]]):
    for c, v in enumerate(row):
        tbl.cell(r, c).text = v
doc.save(f"{OUT}/docx_defaults.docx")
subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", OUT, f"{OUT}/docx_defaults.docx"], capture_output=True)
import pymupdf
pg = pymupdf.open(f"{OUT}/docx_defaults.pdf")[0]
pg.get_pixmap(matrix=pymupdf.Matrix(1.3, 1.3), clip=pymupdf.Rect(0, 0, pg.rect.width, 420)).save(f"{OUT}/docx_defaults.png")
