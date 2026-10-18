# Verification log

Every technique in `references/documents.md` and `references/charts-images.md`
(and the bidi/typography claims marked "verified") was run here, rendered to
PNG, and inspected. Re-run with:

```bash
pip install matplotlib pillow reportlab fpdf2 uharfbuzz weasyprint pymupdf python-docx python-pptx arabic-reshaper python-bidi
(cd node && npm i pptxgenjs docx playwright@1.56.1)
python3 v_matplotlib.py && python3 v_pillow.py && python3 v_pdf.py && python3 v_office.py && python3 v_spacing.py
(cd node && node v_js_office.mjs && node v_pptxgen2.mjs && node measure.mjs)
```

Fonts: Noto Naskh Arabic, IBM Plex Sans Arabic (Google Fonts). Renderer for
Office files: LibreOffice 24.2.7.2 (headless, `--convert-to pdf`), PDFs rasterized with PyMuPDF.

## Versions tested (2026-10-18)

| Library | Version |
|---|---|
| matplotlib | 3.11.2 (bundles libraqm 0.10.5) and 3.10.9 |
| Pillow | 12.3.0, libraqm 0.10.5 |
| reportlab | 5.0.1 |
| fpdf2 | 2.8.9 + uharfbuzz 0.56.3 |
| PyMuPDF | 1.28.2 |
| WeasyPrint | 70.0 |
| arabic-reshaper / python-bidi | 3.0.1 / 0.6.11 |
| python-docx / python-pptx | 1.2.0 / 1.0.2 |
| docx (docx-js) / pptxgenjs | 9.12.0 / 4.0.1 |
| Chromium (Playwright 1.56.1) | build 1194 |
| Node ICU | 77.1 (Node 22.22) |

## Results

| Technique | Result | Evidence |
|---|---|---|
| matplotlib 3.11, raw Arabic string | ✅ shaped + correct order | `matplotlib_naive.png` |
| matplotlib 3.11, reshape+bidi | ❌ **breaks** (reversed, disconnected) | `matplotlib_fixed.png` |
| matplotlib 3.10, raw Arabic | ❌ disconnected letters | `matplotlib310_naive.png` |
| matplotlib 3.10, reshape+bidi | ✅ | `matplotlib310_fixed.png` |
| matplotlib 3.11 PDF backend, raw | ⚠️ shaped, but spacing glitch next to Latin + `،` | `matplotlib_native_pdf.png` |
| Pillow BASIC layout, raw | ❌ | `pillow_basic_naive.png` |
| Pillow BASIC layout, reshape+bidi | ✅ | `pillow_basic_reshaped.png` |
| Pillow RAQM layout, raw + `direction="rtl"` | ✅ | `pillow_raqm_native.png` |
| Pillow RAQM layout, reshape+bidi | ❌ double-processed, reversed | `pillow_raqm_plus_reshape_DOUBLE.png` |
| reportlab `drawString`, raw | ❌ | `reportlab_naive.png` |
| reportlab `drawRightString`, reshape+bidi | ✅ | `reportlab_reshaped.png` |
| reportlab `Paragraph`, reshape+bidi, multi-line | ❌ lines come out bottom-to-top | `reportlab_multiline_wrong.png` |
| reportlab: wrap logical text first, one `Paragraph` per line | ✅ | `reportlab_multiline_fixed.png` |
| reportlab native RTL (`rlbidi`) | ⚪ not tested: `rlbidi` is not on PyPI | – |
| fpdf2 raw | ❌ | `fpdf2_naive.png` |
| fpdf2 `set_text_shaping(...)` (+uharfbuzz) | ✅ incl. `multi_cell` wrapping | `fpdf2_shaping.png`, `fpdf2_multicell.png` |
| PyMuPDF `insert_text` | ❌ | `pymupdf_insert_text.png` |
| PyMuPDF `insert_htmlbox` + `dir="rtl"` | ✅ | `pymupdf_insert_htmlbox.png` |
| WeasyPrint, `<html dir="rtl">` | ✅ | `weasyprint.png` |
| python-docx without bidi | ❌ left aligned, mixed text reordered, LTR table | `docx_naive.png` |
| python-docx `w:bidi` + `w:rtl` + `w:cs` font + `szCs`/`bCs` + `w:bidiVisual` | ✅ | `docx_fixed.png` |
| `w:sz`/`w:b` without `w:szCs`/`w:bCs` | ❌ Arabic stays default size, not bold | `docx_szcs.png` |
| docx-js `bidirectional` + `rightToLeft` + `sizeComplexScript` + `visuallyRightToLeft` | ✅ | `docxjs_fixed.png` |
| Run letter-spacing in docx (LibreOffice) | ❌ breaks joining | `docx_letterspacing.png` |
| docx `w:jc="both"` on RTL paragraph (LibreOffice) | ✅ justified with automatic kashida | `docx_kashida.png` |
| docx `w:jc="highKashida"` (LibreOffice) | ❌ ignored, not justified | `docx_kashida.png` |
| python-pptx `rtl="1"` + `algn="r"` + `a:cs` | ✅ | `pptx_fixed.png` vs `pptx_naive.png` |
| pptxgenjs `rtlMode` on the `addText` call only, runs array | ❌ `rtl="1"` not emitted | `pptxgenjs_naive.png` (same output) |
| pptxgenjs `rtlMode` inside every run's `options` | ✅ | `pptxgenjs_fixed.png` |
| SVG `<text>` without `direction` | ❌ wrong order | `web_svg_canvas.png` row a |
| SVG `direction="rtl"` + `text-anchor="end"` | ❌ text runs off to the right of x | row b, d |
| SVG `direction="rtl"` + `text-anchor="start"` | ✅ right edge at x | row c |
| Canvas `ctx.direction="rtl"` | ✅ (`ltr` reorders wrongly) | `web_svg_canvas.png` |
| Canvas draws before webfont loads | ⚠️ falls back to a serif font | same image |
| Chromium letter-spacing on Arabic | ⚪ Chromium 141 ignores it (stays joined); LibreOffice breaks | `web_typo.png` |
| `font-style: italic` on Arabic | ❌ synthetic slant in the wrong direction | `web_typo.png` |
| Phone / negative number / EN name + number in RTL text, no isolation | ❌ reordered | `measure.mjs` output, `web_bidi.png` |
| Same with `<bdi>` / `dir="ltr"` / LRM | ✅ | same |
| `<input>` with phone, no `dir="ltr"` | ❌ `4567 123 50 966+` | `web_bidi.png` |
| `dir="auto"` on text that starts with an email | ⚠️ becomes LTR | `web_bidi.png` |
| `Intl` `ar` (no region) | Latin digits; `ar-SA`/`ar-EG` Arabic-Indic; `ar-MA/DZ/TN` `1.234,5` | node output in this README's commit |
| `ar-SA` default calendar (ICU 77) | Gregorian; must pass `-u-ca-islamic-umalqura` for Hijri | same |

`measure.mjs` output (x positions in px, RTL paragraph, larger x = further right):

```
raw   "John Smith 3"   3 at 1223, J at 1127  -> 3 is RIGHT of the name (wrong)
<bdi>                  3 at 1127, J at 1142  -> correct
raw   "-5"             - at 1152, 5 at 1142  -> renders "5-" (wrong)
&lrm;-5                - at 1142, 5 at 1149  -> correct
raw   "+966 50 123 4567"  + at 1172, 4567 at 1037 -> groups reversed
<bdi dir=ltr>          + at 1037, 4567 at 1143 -> correct
raw   "--verbose"      -- at 1159, verbose at 1097 -> "verbose--" (wrong)
<code dir=ltr>         -- at 1051, verbose at 1075 -> correct
```

`web_claims.mjs` (Chrome 141, `<html dir="rtl">`):

```
scrollLeft at start 0, at end -400        -> negative scrollLeft in RTL
float: inline-start  -> x=450 (right edge of a 500px viewport)
flex first child     -> x=450 (starts on the right)
justify-content:left -> x=200 (does NOT flip)
range / progress     -> fill from the right (web_range.png)
```

## Snippets in the references are executed verbatim

`v_snippets.py` extracts the fenced `python`, `svg` and `js` blocks from
`references/documents.md` and `references/charts-images.md`, runs them as written
(only font paths substituted), and renders each output to `out/snippet_*.png`.
This caught one bug that is now fixed in the docs: wrapping reportlab text to the
full `doc.width` let the first word drop to the next line (frame padding is 6pt per side).
The JS snippets for docx-js / pptxgenjs are covered by `node/v_js_office.mjs` and `node/v_pptxgen2.mjs`.
