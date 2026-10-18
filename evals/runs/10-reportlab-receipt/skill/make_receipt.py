#!/usr/bin/env python3
"""Generate an Arabic payment receipt (receipt.pdf) with reportlab.

reportlab draws glyphs one by one (no Arabic shaping, no bidi), so every
Arabic string goes through prepare() from shape_text.py. Multi-line text is
wrapped in logical order first, then each line is shaped separately.
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from shape_text import prepare

HERE = Path(__file__).resolve().parent
FONT_DIRS = [Path.home() / ".fonts", Path("/usr/share/fonts/truetype/noto"), HERE]


def find_font(name):
    for d in FONT_DIRS:
        p = d / name
        if p.exists():
            return str(p)
    raise FileNotFoundError(f"Font {name} not found in {FONT_DIRS}")


pdfmetrics.registerFont(TTFont("Naskh", find_font("NotoNaskhArabic-400.ttf")))
pdfmetrics.registerFont(TTFont("Naskh-Bold", find_font("NotoNaskhArabic-700.ttf")))


def ar(text):
    return prepare(text, target="reportlab")


def sar(amount):
    # Western digits, Arabic currency symbol after the number.
    return f"{amount:,.2f} ر.س"


def wrap_rtl(text, font, size, width):
    """Wrap logical (unshaped) text by measuring shaped widths."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if stringWidth(ar(trial), font, size) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    return lines + [cur]


# ---- data -----------------------------------------------------------------
STORE = "متجر الياسمين"
RECEIPT_NO = "5521"
CUSTOMER = "أحمد بن خالد العتيبي"
DATE = "2026/10/18"
ITEMS = [
    ("عطر الياسمين الفاخر 50 مل", 1, 185.00),
    ("صابون طبيعي بزيت الزيتون", 3, 18.50),
    ("شمعة معطرة بالعود", 2, 42.00),
]
THANKS = (
    "شكرًا لتسوقكم من متجر الياسمين، يسعدنا أن نكون جزءًا من يومكم. "
    "نتمنى أن تنال مشترياتكم إعجابكم، ونرحب بزيارتكم مجددًا في أي وقت. "
    "يمكنكم استبدال المنتجات خلال 7 أيام من تاريخ الشراء مع الاحتفاظ بهذا الإيصال."
)

# ---- styles ---------------------------------------------------------------
title = ParagraphStyle("title", fontName="Naskh-Bold", fontSize=20, leading=32, alignment=TA_CENTER)
sub = ParagraphStyle("sub", fontName="Naskh", fontSize=11, leading=19, alignment=TA_CENTER,
                     textColor=colors.HexColor("#555555"))
body = ParagraphStyle("body", fontName="Naskh", fontSize=11, leading=19, alignment=TA_RIGHT)
cell = ParagraphStyle("cell", parent=body, fontSize=10.5, leading=18)
cell_b = ParagraphStyle("cellb", parent=cell, fontName="Naskh-Bold")


def build(out_path):
    doc = SimpleDocTemplate(str(out_path), pagesize=A5,
                            rightMargin=14 * mm, leftMargin=14 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title="Receipt 5521", author=STORE)
    frame_w = doc.width - 12  # frames have 6pt padding on each side

    story = [
        Paragraph(ar(STORE), title),
        Paragraph(ar("إيصال دفع"), sub),
        Spacer(1, 6 * mm),
        Paragraph(ar(f"رقم الإيصال: {RECEIPT_NO}"), body),
        Paragraph(ar(f"التاريخ: {DATE}"), body),
        Paragraph(ar(f"اسم العميل: {CUSTOMER}"), body),
        Spacer(1, 5 * mm),
    ]

    # Table: logical column order is (item, qty, unit price, line total);
    # reversed so the first column sits on the right.
    header = ["الصنف", "الكمية", "سعر الوحدة", "الإجمالي"]
    rows = [[Paragraph(ar(h), cell_b) for h in header]]
    total = 0.0
    for name, qty, price in ITEMS:
        line = qty * price
        total += line
        rows.append([Paragraph(ar(name), cell), Paragraph(str(qty), cell),
                     Paragraph(ar(sar(price)), cell), Paragraph(ar(sar(line)), cell)])
    # Label goes in the cell that becomes the first one of the SPAN after reversal.
    rows.append(["", "", Paragraph(ar("المجموع الكلي"), cell_b),
                 Paragraph(ar(sar(total)), cell_b)])
    rows = [list(reversed(r)) for r in rows]

    n = len(rows)
    col_w = [doc.width * f for f in (0.42, 0.12, 0.23, 0.23)][::-1]
    table = Table(rows, colWidths=col_w, hAlign="RIGHT")
    table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFE7F5")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#7A4E9C")),
        ("LINEBELOW", (0, 1), (-1, n - 3), 0.3, colors.HexColor("#CCCCCC")),
        ("LINEABOVE", (0, n - 1), (-1, n - 1), 0.8, colors.HexColor("#7A4E9C")),
        ("SPAN", (1, n - 1), (3, n - 1)),  # label spans item/qty/unit-price (right side)
        ("BACKGROUND", (0, n - 1), (-1, n - 1), colors.HexColor("#F7F3FA")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [table, Spacer(1, 7 * mm)]

    for line in wrap_rtl(THANKS, "Naskh", 11, frame_w):
        story.append(Paragraph(ar(line), body))

    doc.build(story)
    return total


if __name__ == "__main__":
    out = HERE / "receipt.pdf"
    t = build(out)
    print(f"Wrote {out} (total {sar(t)})")
