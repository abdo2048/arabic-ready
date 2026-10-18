from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

FONT = "Noto Naskh Arabic"

def set_rtl_run(run, size=12, bold=False, color=None):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.bold = bold
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts'); rPr.insert(0, rFonts)
    for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
        rFonts.set(qn(a), FONT)
    if bold:
        rPr.append(OxmlElement('w:bCs'))
    szcs = OxmlElement('w:szCs'); szcs.set(qn('w:val'), str(int(size*2))); rPr.append(szcs)
    rtl = OxmlElement('w:rtl'); rPr.append(rtl)
    lang = OxmlElement('w:lang'); lang.set(qn('w:bidi'), 'ar-EG'); rPr.append(lang)
    if color: run.font.color.rgb = RGBColor.from_string(color)

def set_bidi(p, align=WD_ALIGN_PARAGRAPH.RIGHT):
    pPr = p._element.get_or_add_pPr()
    bidi = OxmlElement('w:bidi'); pPr.insert(0, bidi)
    # In a bidi paragraph the default (start) alignment is the right edge; jc="right" would flip to the left.
    if align != WD_ALIGN_PARAGRAPH.RIGHT:
        p.alignment = align

def para(doc, text, size=12, bold=False, align=WD_ALIGN_PARAGRAPH.RIGHT, style=None, color=None, after=6):
    p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    set_bidi(p, align)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.15
    set_rtl_run(p.add_run(text), size, bold, color)
    return p

def shade(cell, hexcolor):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), hexcolor)
    tcPr.append(shd)

doc = Document()
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
for m in ('left_margin', 'right_margin'): setattr(sec, m, Cm(2.2))
sec.top_margin = sec.bottom_margin = Cm(2)
# RTL section
sectPr = sec._sectPr
sectPr.append(OxmlElement('w:bidi'))

# Default style: Arabic font + RTL
st = doc.styles['Normal']
st.font.name = FONT
rpr = st.element.get_or_add_rPr()
rf = rpr.find(qn('w:rFonts'))
for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'): rf.set(qn(a), FONT)
lang = OxmlElement('w:lang'); lang.set(qn('w:val'), 'ar-EG'); lang.set(qn('w:bidi'), 'ar-EG'); rpr.append(lang)


# custom RTL bullet list definition
from docx.opc.constants import RELATIONSHIP_TYPE as RT
numbering = doc.part.numbering_part.element
absId = 90
an = OxmlElement('w:abstractNum'); an.set(qn('w:abstractNumId'), str(absId))
lvl = OxmlElement('w:lvl'); lvl.set(qn('w:ilvl'), '0')
for tag, val in (('w:start','1'),('w:numFmt','bullet'),('w:lvlText','●'),('w:lvlJc','left')):
    e = OxmlElement(tag); e.set(qn('w:val'), val); lvl.append(e)
lp = OxmlElement('w:pPr'); lp.append(OxmlElement('w:bidi'))
li = OxmlElement('w:ind'); li.set(qn('w:right'), '567'); li.set(qn('w:hanging'), '284'); lp.append(li); lvl.append(lp)
lr = OxmlElement('w:rPr'); f = OxmlElement('w:rFonts')
for a in ('w:ascii','w:hAnsi','w:cs'): f.set(qn(a), 'Arial')
lr.append(f); c = OxmlElement('w:color'); c.set(qn('w:val'), '1F3864'); lr.append(c); lr.append(OxmlElement('w:rtl')); lvl.append(lr)
an.append(lvl)
first_num = numbering.find(qn('w:num'))
if first_num is not None: first_num.addprevious(an)
else: numbering.append(an)
BULLET_NUM = 90
num = OxmlElement('w:num'); num.set(qn('w:numId'), str(BULLET_NUM))
aid = OxmlElement('w:abstractNumId'); aid.set(qn('w:val'), str(absId)); num.append(aid); numbering.append(num)

para(doc, "شركة النيل للصناعات الغذائية — القاهرة", 11, color="666666", after=0)
para(doc, "تقرير الموارد البشرية للربع الثالث 2026", 22, True, WD_ALIGN_PARAGRAPH.CENTER, color="1F3864", after=2)
para(doc, "الفترة: يوليو – سبتمبر 2026", 11, False, WD_ALIGN_PARAGRAPH.CENTER, color="666666", after=14)

para(doc, "ملخص الأداء", 15, True, color="1F3864", after=4)
para(doc, "شهد الربع الثالث استقرارًا نسبيًا في القوى العاملة، إذ بلغ معدل دوران الموظفين 12% مقارنةً بـ 15% في الربع السابق، "
          "ويُعزى هذا التحسن إلى مراجعة هيكل الأجور وتوسيع برامج التدريب الداخلي، خاصةً في إدارتي المبيعات والإنتاج.")
para(doc, "وفي إطار خطة التوظيف لعام 2026، تستهدف الشركة تعيين 85 موظفًا جديدًا موزعين على الإدارات الأربع، مع التركيز على "
          "الكفاءات التقنية في مصنع العاشر من رمضان، وإطلاق برنامج للخريجين الجدد بالتعاون مع الجامعات المصرية.", after=10)

para(doc, "أبرز الإنجازات", 15, True, color="1F3864", after=4)
for t in ["إطلاق منصة إلكترونية للتقييم السنوي للأداء شملت جميع الموظفين.",
          "تدريب 240 موظفًا على مهارات السلامة المهنية والقيادة.",
          "رفع نسبة تمثيل المرأة في المناصب الإشرافية إلى 28%."]:
    bp = para(doc, t, after=3)
    pPr = bp._element.get_or_add_pPr()
    numPr = OxmlElement('w:numPr')
    il = OxmlElement('w:ilvl'); il.set(qn('w:val'), '0'); numPr.append(il)
    ni = OxmlElement('w:numId'); ni.set(qn('w:val'), str(BULLET_NUM)); numPr.append(ni)
    pPr.append(numPr)
    ind = OxmlElement('w:ind'); ind.set(qn('w:right'), '567'); ind.set(qn('w:hanging'), '284'); pPr.append(ind)

para(doc, "", after=4)
para(doc, "عدد الموظفين حسب الإدارة", 15, True, color="1F3864", after=6)

rows = [("الإدارة", "عدد الموظفين", "التعيينات الجديدة", "نسبة الدوران"),
        ("الإنتاج", "320", "18", "14%"),
        ("المبيعات والتسويق", "145", "11", "13%"),
        ("المالية والإدارة", "60", "3", "8%"),
        ("تكنولوجيا المعلومات", "45", "6", "10%"),
        ("الإجمالي", "570", "38", "12%")]
tbl = doc.add_table(rows=len(rows), cols=4)
tbl.style = 'Table Grid'
tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
tblPr = tbl._tbl.tblPr
tblPr.append(OxmlElement('w:bidiVisual'))
for i, r in enumerate(rows):
    for j, val in enumerate(r):
        c = tbl.cell(i, j)
        c.width = Cm(5.2) if j == 0 else Cm(3.6)
        p = c.paragraphs[0]
        set_bidi(p, WD_ALIGN_PARAGRAPH.RIGHT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER)
        p.paragraph_format.space_after = Pt(2); p.paragraph_format.space_before = Pt(2)
        head = i == 0; total = i == len(rows) - 1
        set_rtl_run(p.add_run(val), 11, head or total, "FFFFFF" if head else None)
        if head: shade(c, "1F3864")
        elif total: shade(c, "D9E2F3")
        elif i % 2 == 0: shade(c, "F2F2F2")

para(doc, "", after=2)
para(doc, "إعداد: إدارة الموارد البشرية — أكتوبر 2026", 10, color="888888", after=0)

P_ORDER = "pStyle keepNext keepLines pageBreakBefore framePr widowControl numPr suppressLineNumbers pBdr shd tabs suppressAutoHyphens kinsoku wordWrap overflowPunct topLinePunct autoSpaceDE autoSpaceDN bidi adjustRightInd snapToGrid spacing ind contextualSpacing mirrorIndents suppressOverlap jc textDirection textAlignment textboxTightWrap outlineLvl divId cnfStyle rPr sectPr pPrChange".split()
R_ORDER = "rStyle rFonts b bCs i iCs caps smallCaps strike dstrike outline shadow emboss imprint noProof snapToGrid vanish webHidden color spacing w kern position sz szCs highlight u effect bdr shd fitText vertAlign rtl cs em lang eastAsianLayout specVanish oMath".split()
T_ORDER = "tblStyle tblpPr tblOverlap bidiVisual tblStyleRowBandSize tblStyleColBandSize tblW jc tblCellSpacing tblInd tblBorders shd tblLayout tblCellMar tblLook tblCaption tblDescription".split()
S_ORDER = "headerReference footerReference footnotePr endnotePr type pgSz pgMar paperSrc pgBorders lnNumType pgNumType cols formProt vAlign noEndnote titlePg textDirection bidi rtlGutter docGrid printerSettings sectPrChange".split()
def reorder(el, order):
    kids = list(el)
    key = lambda k: order.index(k.tag.split('}')[1]) if k.tag.split('}')[1] in order else len(order)
    kids.sort(key=key)
    for k in kids: el.remove(k)
    for k in kids: el.append(k)
for part in [doc.element, doc.styles.element]:
    for e in part.iter(qn('w:pPr')): reorder(e, P_ORDER)
    for e in part.iter(qn('w:rPr')): reorder(e, R_ORDER)
    for e in part.iter(qn('w:tblPr')): reorder(e, T_ORDER)
    for e in part.iter(qn('w:sectPr')): reorder(e, S_ORDER)
doc.save("report.docx")
