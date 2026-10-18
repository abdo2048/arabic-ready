#!/usr/bin/env python3
"""Render every eval run to PNG and build baseline-vs-skill comparison images.

    python evals/harness/render.py            # all runs
    python evals/harness/render.py 03-invoice-pdf

For each evals/runs/<id>/<arm>/ it writes render.png (or render-*.png) and
rtl_check.txt, then evals/results/<id>.png with both arms side by side.
Renderers: Chromium via Playwright (HTML, text), LibreOffice (docx/pptx),
PyMuPDF (PDF). Tailwind CDN pages are compiled locally with tailwindcss v3.
"""
import glob
import html
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
EVALS = os.path.dirname(HERE)
ROOT = os.path.dirname(EVALS)
RUNS = os.path.join(EVALS, "runs")
RESULTS = os.path.join(EVALS, "results")
CHECK = os.path.join(ROOT, "skills", "arabic-ready", "scripts", "rtl_check.py")
PROMPTS = {p["id"]: p for p in json.load(open(os.path.join(EVALS, "prompts.json"), encoding="utf-8"))}
LABEL_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def sh(*cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def newest(d, pattern):
    files = [f for f in glob.glob(os.path.join(d, "**", pattern), recursive=True)
             if "/node_modules/" not in f and not os.path.basename(f).startswith(("render", "_"))]
    return max(files, key=os.path.getmtime) if files else None


def compile_tailwind(html_path):
    """Return HTML with the Tailwind CDN script replaced by compiled CSS (CDNs are blocked here)."""
    src = open(html_path, encoding="utf-8").read()
    if "tailwindcss" not in src:
        return None
    config = ""
    m = re.search(r"tailwind\.config\s*=\s*(\{.*?\})\s*;?\s*</script>", src, re.S)
    cfg_path = os.path.join(os.path.dirname(html_path), "_tw.config.js")
    with open(cfg_path, "w") as f:
        f.write("module.exports = " + (m.group(1) if m else "{}") + ";\n"
                f"module.exports.content = [{json.dumps(html_path)}];\n")
    inp = os.path.join(os.path.dirname(html_path), "_tw.in.css")
    out = os.path.join(os.path.dirname(html_path), "_tw.out.css")
    with open(inp, "w") as f:
        f.write("@tailwind base;\n@tailwind components;\n@tailwind utilities;\n")
    # also include any <style type="text/tailwindcss"> blocks
    for block in re.findall(r'<style[^>]*type="text/tailwindcss"[^>]*>(.*?)</style>', src, re.S):
        with open(inp, "a") as f:
            f.write(block)
    r = sh("npx", "tailwindcss", "-c", cfg_path, "-i", inp, "-o", out, cwd=HERE)
    if r.returncode:
        print("tailwind failed:", r.stderr[-500:])
        return None
    css = open(out, encoding="utf-8").read()
    src = re.sub(r'<script[^>]*cdn\.tailwindcss\.com[^>]*>\s*</script>', "", src)
    src = re.sub(r'<script[^>]*@tailwindcss/browser[^>]*>\s*</script>', "", src)
    src = src.replace("</head>", f"<style>{css}</style></head>", 1)
    compiled = os.path.join(os.path.dirname(html_path), "_compiled.html")
    with open(compiled, "w", encoding="utf-8") as f:
        f.write(src)
    return compiled


def screenshot(url, out, width=1280, height=900, full=True):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        pg.goto(url, wait_until="networkidle")
        pg.wait_for_timeout(500)
        pg.screenshot(path=out, full_page=full)
        b.close()


def pdf_png(pdf, out, zoom=1.5):
    import pymupdf
    doc = pymupdf.open(pdf)
    doc[0].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(out)


def office_png(path, out):
    d = os.path.dirname(path)
    sh("soffice", "--headless", "--convert-to", "pdf", "--outdir", os.path.join(d, "_pdf"), path)
    pdf = os.path.join(d, "_pdf", os.path.splitext(os.path.basename(path))[0] + ".pdf")
    if os.path.exists(pdf):
        pdf_png(pdf, out, 1.3)


def whatsapp_png(txt, out):
    """Approximate a chat bubble: every line is its own paragraph with dir=auto (first strong char)."""
    lines = open(txt, encoding="utf-8").read().rstrip("\n").split("\n")
    body = "".join(f'<div dir="auto" class="l">{html.escape(l) or "&nbsp;"}</div>' for l in lines)
    page = f"""<!doctype html><html><meta charset="utf-8"><style>
    body{{margin:0;background:#efeae2;font-family:'Noto Sans Arabic','Noto Color Emoji',sans-serif;padding:24px}}
    .b{{background:#fff;border-radius:10px;padding:10px 14px;max-width:440px;margin-left:auto;font-size:17px;line-height:1.6;box-shadow:0 1px 1px #0002}}
    .l{{unicode-bidi:plaintext;text-align:start;white-space:pre-wrap}}</style>
    <div class="b">{body}</div></html>"""
    tmp = os.path.join(os.path.dirname(txt), "_chat.html")
    open(tmp, "w", encoding="utf-8").write(page)
    screenshot("file://" + tmp, out, width=520, height=200)


def render_arm(run_id, arm):
    d = os.path.join(RUNS, run_id, arm)
    kind = PROMPTS[run_id]["render"]
    out = os.path.join(d, "render.png")
    try:
        if kind == "html":
            page = newest(d, "index.html") or newest(d, "*.html")
            if page:
                compiled = compile_tailwind(page) or page
                screenshot("file://" + compiled, out)
                screenshot("file://" + compiled, os.path.join(d, "render-mobile.png"), width=390, height=844)
        elif kind == "pdf":
            pdf = newest(d, "invoice.pdf") or newest(d, "*.pdf")
            if pdf:
                pdf_png(pdf, out)
        elif kind == "png":
            png = newest(d, "chart.png") or newest(d, "post.png") or newest(d, "*.png")
            if png:
                Image.open(png).convert("RGB").save(out)
        elif kind in ("docx", "pptx"):
            f = newest(d, f"*.{kind}")
            if f:
                office_png(f, out)
        elif kind == "text":
            f = newest(d, "message.txt") or newest(d, "*.txt")
            if f:
                whatsapp_png(f, out)
    except Exception as e:  # keep going; the comparison shows "no render"
        print(f"{run_id}/{arm}: render error {e}")
    code = [f for f in glob.glob(os.path.join(d, "**", "*"), recursive=True)
            if os.path.splitext(f)[1] in (".html", ".tsx", ".jsx", ".css")
            and not os.path.basename(f).startswith("_") and "/node_modules/" not in f]
    report = sh(sys.executable, CHECK, *code).stdout if code else "no code files\n"
    report = report.replace(d + "/", "")
    open(os.path.join(d, "rtl_check.txt"), "w", encoding="utf-8").write(report)
    return out if os.path.exists(out) else None


def label(img, text, color):
    f = ImageFont.truetype(LABEL_FONT, 28)
    bar = Image.new("RGB", (img.width, 52), color)
    ImageDraw.Draw(bar).text((16, 10), text, font=f, fill="white")
    c = Image.new("RGB", (img.width, img.height + 52), "white")
    c.paste(bar, (0, 0)); c.paste(img, (0, 52))
    return c


def side_by_side(run_id, left, right, max_h=1400, width=900):
    ims = []
    for path, text, color in ((left, "WITHOUT skill", "#b42318"), (right, "WITH arabic-ready", "#067647")):
        if path and os.path.exists(path):
            im = Image.open(path).convert("RGB")
            im = im.resize((width, int(im.height * width / im.width)))
            im = im.crop((0, 0, width, min(im.height, max_h)))
        else:
            im = Image.new("RGB", (width, 300), "#eee")
            ImageDraw.Draw(im).text((20, 140), "no output", fill="black")
        ims.append(label(im, text, color))
    h = max(i.height for i in ims)
    c = Image.new("RGB", (width * 2 + 24, h), "white")
    c.paste(ims[0], (0, 0)); c.paste(ims[1], (width + 24, 0))
    os.makedirs(RESULTS, exist_ok=True)
    c.save(os.path.join(RESULTS, f"{run_id}.png"), optimize=True)


def main(ids):
    for run_id in ids or sorted(PROMPTS):
        outs = {arm: render_arm(run_id, arm) for arm in ("baseline", "skill")}
        if PROMPTS[run_id]["render"] != "static":
            side_by_side(run_id, outs["baseline"], outs["skill"])
        print(run_id, {k: bool(v) for k, v in outs.items()})


if __name__ == "__main__":
    main(sys.argv[1:])
