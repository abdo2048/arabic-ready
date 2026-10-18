# Evals

Twelve realistic prompts, each run twice by a fresh subagent (same model):
**without** the skill, and **with** it (told to read `SKILL.md` first, as an installed skill would).
Every output was rendered (Chromium for HTML and chat text, LibreOffice for docx/pptx,
PyMuPDF for PDF) and placed side by side in `results/<id>.png`. Code outputs were also
linted with `rtl_check.py` (`runs/<id>/<arm>/rtl_check.txt`).

- `prompts.json`: the prompts (4 written in Arabic, 8 in English)
- `runs/<id>/{baseline,skill}/`: everything each agent produced
- `harness/render.py`: renders all runs and builds `results/*.png`
- `verify/`: the library-behavior verification log behind `references/` (see `verify/README.md`)

Re-run the rendering: `python evals/harness/render.py` (needs Playwright + Chromium, LibreOffice, PyMuPDF; `cd evals/harness && npm i` for the Tailwind compiler).

## Results

Round 1 (prompts 01–09) covered the requested output types. Round 2 (10–12) named a library
where common knowledge is a trap: reportlab, pptxgenjs, and matplotlib pinned to 3.10.

| # | Prompt | Without skill | With skill | Verdict |
|---|---|---|---|---|
| 01 | Pricing page, Tailwind | ✅ correct RTL, logical classes, mirrored arrows | ✅ same; Western digits, phone/`SSO` isolated | tie |
| 02 | Login form (Arabic prompt) | ✅ renders correctly; `rtl_check`: 2 errors (`text-align: right`) | ✅ renders correctly; lint clean | skill slightly better |
| 03 | Invoice PDF | ✅ WeasyPrint, correct | ✅ WeasyPrint, correct | tie |
| 04 | matplotlib bar chart | ✅ correct (agent tested and noticed reshaping breaks 3.11) | ✅ correct + RTL value axis and legend | tie / slight |
| 05 | Word report | ✅ correct (built a custom RTL numbering to get bullets right) | ✅ correct (RTL set once in docDefaults); Arabic-Indic digits for an Egyptian formal report | tie |
| 06 | PowerPoint slide | ✅ correct | ✅ correct | tie |
| 07 | Instagram image, Pillow | ✅ correct (raqm native) | ✅ correct (raqm native, fallback to `prepare()`) | tie |
| 08 | React Native screen (static review) | ⚠️ `direction:'rtl'` on the root view; app-wide RTL (`I18nManager.forceRTL`) only described in a comment; hard-coded `chevron-back` (lint warning, wrong if the app ever runs LTR) | ✅ `forceRTL` + reload, start/end styles, mirrored directional icons only; lint clean | skill better |
| 09 | WhatsApp message | ✅ readable; lines start with emoji, phone on its own line | ✅ phone isolated with LRI/PDI, no leading emoji, MSA | skill slightly better |
| 10 | reportlab receipt | ✅ correct incl. its own wrap-first fix; tashkeel silently dropped (`شكراً` → `شكرا`) | ✅ correct, tashkeel kept | skill slightly better |
| 11 | pptxgenjs slide | ✅ correct (found the per-run `rtlMode` issue by testing) | ✅ correct first try | tie |
| 12 | matplotlib 3.10, horizontal bars | ✅ correct | ✅ correct | tie |

**Honest summary.** On this model the baseline was already good: no eval produced visibly broken Arabic
without the skill. The skill did not rescue failures. What it changed:
- **Fewer latent bugs**: lint-clean output (02, 08), Arabic text in plain-text channels that can't flip (09), tashkeel preserved (10).
- **Fewer discoveries by trial and error**: baselines found the matplotlib 3.11 double-shaping, the
  pptxgenjs `rtlMode` quirk and the docx bullet problem by rendering, failing and retrying. With the
  skill these were right on the first attempt.
- **Better defaults**: RTL chart axes, digit choice by market, logical properties everywhere.
- **Cost**: skill runs used about 22% more tokens on average (785k vs 642k total), mostly from reading references.

The before/after images in `examples/` therefore come from `verify/`: the same Arabic text sent
through each library the common way and the way the skill prescribes. That's where broken Arabic is
real and reproducible (reportlab, fpdf2, PyMuPDF, Pillow+raqm with reshaping, matplotlib 3.11 with
reshaping, Office files without RTL, web text without isolation).

## What the evals changed in the skill
- **Bug fixed:** `shape_text.py --check` crashed (`importlib.util` not imported). Found by the
  12-skill agent; added a subprocess test that runs it in a fresh interpreter.
- **Wrong claim fixed:** `bidi.md` said `25%` stays `25%`. Every renderer shows `%25` inside RTL text.
  Now documented as the normal display, with the isolate to use if a brand wants `25%`. Two agents
  had "fixed" it by hand.
- **Render step made concrete:** two skill agents skipped the visual check because they couldn't find
  a browser. `SKILL.md` now gives copy-paste commands (Playwright CLI, WeasyPrint fallback,
  LibreOffice, PyMuPDF).
- Harness bug (not the skill): the Tailwind config regex missed a trailing `;`. Fixed and re-rendered.

## Caveats
- One run per arm, with no variance estimate. Grading is visual inspection by the author plus `rtl_check`.
- The sandbox had Arabic Google Fonts installed and current library versions, which helps the baseline.
- Same model for both arms. Weaker or older models, or users who don't render their output, are where
  the skill is expected to matter more. That was not measured here.
- React Native and Flutter output was reviewed statically, not run on a device.
