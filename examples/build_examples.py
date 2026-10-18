#!/usr/bin/env python3
"""Build the before/after images in examples/ from real renders.

Inputs come from evals/verify/out (run the v_*.py scripts there first): the
same Arabic text sent through each library the naive way and the way the skill
prescribes. Web examples are rendered live in Chromium. Run: python examples/build_examples.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
V = os.path.join(ROOT, "evals", "verify", "out")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
RED, GREEN, INK = "#b42318", "#067647", "#1d2939"


def trim(im, pad=12):
    from PIL import ImageChops
    bg = Image.new("RGB", im.size, im.getpixel((0, 0)))
    box = ImageChops.difference(im.convert("RGB"), bg).getbbox()
    if not box:
        return im
    return im.crop((max(0, box[0] - pad), max(0, box[1] - pad),
                    min(im.width, box[2] + pad), min(im.height, box[3] + pad)))


def fit(im, w, h):
    im = im.convert("RGB")
    s = min(w / im.width, h / im.height)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    c = Image.new("RGB", (w, h), "white")
    c.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    return c


def grid(rows, out, title, cell=(700, 170), left="Typical code", right="With arabic-ready"):
    """rows: [(label, before_img, after_img)]"""
    cw, ch = cell
    lab_w, head_h, title_h, gap = 210, 56, 70, 14
    W = lab_w + 2 * cw + 3 * gap
    H = title_h + head_h + len(rows) * (ch + gap) + gap
    c = Image.new("RGB", (W, H), "#f8f9fb")
    d = ImageDraw.Draw(c)
    d.text((gap, 18), title, font=ImageFont.truetype(FONT_B, 30), fill=INK)
    x1, x2 = lab_w + gap, lab_w + cw + 2 * gap
    for x, text, color in ((x1, "✗  " + left, RED), (x2, "✓  " + right, GREEN)):
        d.rounded_rectangle((x, title_h, x + cw, title_h + head_h - 10), 10, fill=color)
        d.text((x + 18, title_h + 9), text, font=ImageFont.truetype(FONT_B, 24), fill="white")
    y = title_h + head_h
    for label, a, b in rows:
        d.multiline_text((gap, y + 12), label, font=ImageFont.truetype(FONT, 19), fill=INK, spacing=6)
        for x, im, color in ((x1, a, RED), (x2, b, GREEN)):
            c.paste(fit(im, cw - 4, ch - 4), (x + 2, y + 2))
            d.rounded_rectangle((x, y, x + cw, y + ch), 8, outline=color, width=3)
        y += ch + gap
    c.save(os.path.join(HERE, out), optimize=True)
    print("wrote", out)


def side_by_side(a, b, out, title, w=760, max_h=900, left="Without the skill", right="With arabic-ready"):
    ims = []
    for im in (a, b):
        im = im.convert("RGB")
        im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
        ims.append(im.crop((0, 0, w, min(im.height, max_h))))
    h = max(i.height for i in ims)
    gap, top = 20, 130
    c = Image.new("RGB", (2 * w + 3 * gap, h + top + gap), "#f8f9fb")
    d = ImageDraw.Draw(c)
    d.text((gap, 18), title, font=ImageFont.truetype(FONT_B, 30), fill=INK)
    for i, (im, text, color) in enumerate(((ims[0], "✗  " + left, RED), (ims[1], "✓  " + right, GREEN))):
        x = gap + i * (w + gap)
        d.rounded_rectangle((x, 66, x + w, 116), 10, fill=color)
        d.text((x + 18, 76), text, font=ImageFont.truetype(FONT_B, 24), fill="white")
        c.paste(im, (x, top))
        d.rectangle((x, top, x + w, top + im.height), outline=color, width=3)
    c.save(os.path.join(HERE, out), optimize=True)
    print("wrote", out)


def load(*p):
    return Image.open(os.path.join(*p))


def web_example():
    """Same Arabic UI snippets, raw vs fixed, rendered in Chromium."""
    from playwright.sync_api import sync_playwright
    fonts = os.path.expanduser("~/.fonts")
    css = f"""@font-face{{font-family:Plex;src:url(file://{fonts}/IBMPlexSansArabic-400.ttf)}}
    body{{margin:0;font-family:Plex,sans-serif;font-size:22px;background:#fff;width:640px}}
    .r{{padding:12px 18px;border-bottom:1px solid #eee;line-height:1.7}} input{{font:inherit;width:300px;padding:4px 8px}}
    code{{font-family:monospace;background:#f2f4f7;padding:0 4px}} .k{{color:#667085;font-size:15px}}"""
    raw = f"""<html dir="rtl" lang="ar"><style>{css}</style>
    <div class=r><span class=k>رقم الجوال</span><br><input value="+966 50 123 4567"></div>
    <div class=r>اتصل بنا على +966 50 123 4567.</div>
    <div class=r>درجة الحرارة اليوم -5 درجات</div>
    <div class=r>أضف الخيار <code>--verbose</code> لعرض التفاصيل</div>
    <div class=r>نشر John Smith 3 منشورات جديدة</div>
    <div class=r><a href=#>التالي →</a></div></html>"""
    fixed = f"""<html dir="rtl" lang="ar"><style>{css}</style>
    <div class=r><span class=k>رقم الجوال</span><br><input dir="ltr" style="text-align:right" value="+966 50 123 4567"></div>
    <div class=r>اتصل بنا على <bdi dir="ltr">+966 50 123 4567</bdi>.</div>
    <div class=r>درجة الحرارة اليوم &lrm;-5 درجات</div>
    <div class=r>أضف الخيار <code dir="ltr">--verbose</code> لعرض التفاصيل</div>
    <div class=r>نشر <bdi>John Smith</bdi> 3 منشورات جديدة</div>
    <div class=r><a href=#>التالي ←</a></div></html>"""
    shots = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for name, html in (("raw", raw), ("fixed", fixed)):
            path = os.path.join(HERE, f"_web_{name}.html")
            open(path, "w", encoding="utf-8").write(html)
            pg = b.new_page(viewport={"width": 640, "height": 300}, device_scale_factor=2)
            pg.goto("file://" + path); pg.wait_for_timeout(300)
            png = path[:-5] + ".png"
            pg.screenshot(path=png, full_page=True)
            shots.append(Image.open(png).copy())
            os.remove(path); os.remove(png)
        b.close()
    side_by_side(shots[0], shots[1], "web-bidi.png",
                 "Mixed Arabic + numbers in a web page (Chromium)", w=640,
                 left="Raw markup", right="With arabic-ready")


def main():
    web_example()
    # PDF / chart / image libraries: real renders from evals/verify
    grid([
        ("matplotlib 3.11\n(reshape + bidi,\nthe classic advice)", trim(load(V, "matplotlib_fixed.png")), trim(load(V, "matplotlib_naive.png"))),
        ("Pillow + raqm\n(reshape + bidi)", trim(load(V, "pillow_raqm_plus_reshape_DOUBLE.png").crop((0, 18, 760, 90))), trim(load(V, "pillow_raqm_native.png").crop((0, 18, 760, 90)))),
        ("reportlab", trim(load(V, "reportlab_naive.png")), trim(load(V, "reportlab_reshaped.png"))),
        ("reportlab\nmulti-line", trim(load(V, "reportlab_multiline_wrong.png")), trim(load(V, "reportlab_multiline_fixed.png"))),
        ("fpdf2", trim(load(V, "fpdf2_naive.png")), trim(load(V, "fpdf2_shaping.png"))),
        ("PyMuPDF", trim(load(V, "pymupdf_insert_text.png")), trim(load(V, "pymupdf_insert_htmlbox.png"))),
    ], "pdf-charts.png", "Arabic through Python PDF, chart and image libraries", cell=(700, 190))
    grid([
        ("Word (.docx)\npython-docx", trim(load(V, "docx_naive.png")), trim(load(V, "docx_fixed.png"))),
        ("Word: bold / size\nwithout bCs / szCs", trim(load(V, "docx_szcs.png")).crop((0, 0, trim(load(V, "docx_szcs.png")).width, trim(load(V, "docx_szcs.png")).height // 2)), trim(load(V, "docx_szcs.png")).crop((0, trim(load(V, "docx_szcs.png")).height // 2, trim(load(V, "docx_szcs.png")).width, trim(load(V, "docx_szcs.png")).height))),
        ("PowerPoint\npython-pptx", trim(load(V, "pptx_naive.png")), trim(load(V, "pptx_fixed.png"))),
        ("PowerPoint\npptxgenjs", trim(load(V, "pptxgenjs_naive.png")), trim(load(V, "pptxgenjs_fixed.png"))),
    ], "office.png", "Arabic in Word and PowerPoint (rendered with LibreOffice)", cell=(700, 230))

if __name__ == "__main__":
    main()
