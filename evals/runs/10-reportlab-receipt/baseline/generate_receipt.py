"""Generate an Arabic payment receipt PDF (receipt.pdf) with reportlab.

Arabic needs two preprocessing steps before reportlab can draw it:
  1. arabic_reshaper  -> picks the correct contextual glyph forms (joined letters)
  2. python-bidi      -> reorders the logical string into visual (RTL) order

Wrapping caveat: reportlab's Paragraph wraps in visual order, which would put
the *end* of a sentence on the first line. So we wrap the logical text ourselves
(measuring shaped widths) and only then reorder each line individually.
"""
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent / "receipt.pdf"

# IBM Plex Sans Arabic covers Arabic + Latin + digits, so mixed strings render in one font.
FONT_DIRS = [Path.home() / ".fonts", Path("/usr/share/fonts")]


def find_font(name):
    for d in FONT_DIRS:
        hits = list(d.rglob(name))
        if hits:
            return str(hits[0])
    raise FileNotFoundError(name)


pdfmetrics.registerFont(TTFont("Arabic", find_font("IBMPlexSansArabic-400.ttf")))
pdfmetrics.registerFont(TTFont("Arabic-Bold", find_font("IBMPlexSansArabic-700.ttf")))


def ar(text: str) -> str:
    """Shape + reorder a single line of Arabic for display."""
    return get_display(arabic_reshaper.reshape(text))


def ltr(text: str) -> str:
    """Force a left-to-right run (dates, codes) inside RTL text.

    python-bidi treats "2026-10-18" as separate numbers and flips it to
    "18-10-2026"; an LRE...PDF embedding keeps it intact (python-bidi does not
    support the newer LRI/PDI isolates).
    """
    return "\u202a" + text + "\u202c"


def wrap_arabic(text: str, font: str, size: float, max_width: float) -> list[str]:
    """Wrap logical-order text into lines that fit max_width, return display-ready lines."""
    lines, current = [], []
    for word in text.split():
        trial = " ".join(current + [word])
        if current and pdfmetrics.stringWidth(ar(trial), font, size) > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return [ar(line) for line in lines]


def P(text, style):
    return Paragraph(escape(ar(text)), style)


# ---- receipt data ---------------------------------------------------------
store_name = "متجر الياسمين"
receipt_no = "5521"
customer = "أحمد بن سعيد العتيبي"
date = "2026-10-18"
items = [
    ("زيت زيتون بكر ممتاز", 2, 35.00),
    ("عسل سدر طبيعي", 1, 120.00),
    ("قهوة عربية بالهيل", 3, 28.50),
]
thank_you = (
    "شكراً لتسوقكم في متجر الياسمين. نقدّر ثقتكم بنا ونتطلع إلى خدمتكم مجدداً، "
    "ويسعدنا استقبال ملاحظاتكم واقتراحاتكم في أي وقت لنواصل تقديم أفضل المنتجات "
    "وأجود الخدمات لكم ولعائلاتكم."
)


def sar(amount: float) -> str:
    return f"{amount:,.2f} SAR"


# ---- styles ---------------------------------------------------------------
title = ParagraphStyle("title", fontName="Arabic-Bold", fontSize=20, leading=28, alignment=TA_CENTER)
sub = ParagraphStyle("sub", fontName="Arabic", fontSize=11, leading=16, alignment=TA_CENTER,
                     textColor=colors.HexColor("#555555"))
body = ParagraphStyle("body", fontName="Arabic", fontSize=11, leading=18, alignment=TA_RIGHT)
cell = ParagraphStyle("cell", fontName="Arabic", fontSize=10.5, leading=15, alignment=TA_RIGHT)
cell_c = ParagraphStyle("cellc", parent=cell, alignment=TA_CENTER)
head = ParagraphStyle("head", parent=cell, fontName="Arabic-Bold", textColor=colors.white)
head_c = ParagraphStyle("headc", parent=head, alignment=TA_CENTER)
total_st = ParagraphStyle("total", parent=cell, fontName="Arabic-Bold", fontSize=12, leading=18)


def build():
    doc = SimpleDocTemplate(str(OUT), pagesize=A5, rightMargin=14 * mm, leftMargin=14 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title="Receipt 5521", author=store_name)
    width = doc.width
    story = [
        P(store_name, title),
        P("إيصال دفع", sub),
        Spacer(1, 6 * mm),
        P(f"رقم الإيصال: {receipt_no}", body),
        P(f"التاريخ: {ltr(date)}", body),
        P(f"اسم العميل: {customer}", body),
        Spacer(1, 5 * mm),
    ]

    # Table: columns are listed left->right, so for RTL reading the first logical
    # column (item name) goes on the far right.
    data = [[Paragraph(escape(ar("الإجمالي")), head_c), Paragraph(escape(ar("سعر الوحدة")), head_c),
             Paragraph(escape(ar("الكمية")), head_c), Paragraph(escape(ar("الصنف")), head)]]
    total = 0.0
    for name, qty, price in items:
        line_total = qty * price
        total += line_total
        data.append([Paragraph(sar(line_total), cell_c), Paragraph(sar(price), cell_c),
                     Paragraph(str(qty), cell_c), P(name, cell)])
    data.append([Paragraph(sar(total), total_st), "", "", P("المجموع الكلي", total_st)])

    col_w = [width * 0.24, width * 0.24, width * 0.14, width * 0.38]
    table = Table(data, colWidths=col_w)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E6B5E")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F2F7F5")]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E3EFEA")),
        ("SPAN", (1, -1), (2, -1)),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9DB8B0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [table, Spacer(1, 7 * mm)]

    # Thank-you paragraph: pre-wrapped in logical order, one Paragraph per line.
    for line in wrap_arabic(thank_you, body.fontName, body.fontSize, width):
        story.append(Paragraph(escape(line), body))

    doc.build(story)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
