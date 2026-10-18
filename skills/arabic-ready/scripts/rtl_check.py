#!/usr/bin/env python3
"""Lint web, React Native and Flutter code for RTL (Arabic) bugs.

Usage:
    python rtl_check.py <file-or-folder> [more paths] [--json] [--strict]

Checks:
  physical-css       margin-left, padding-right, left:, text-align: left, float, border-left ...
  physical-tailwind  ml-*, pr-*, left-*, text-left, rounded-l-*, border-r-* ...
  physical-style     marginLeft / paddingRight in JS style objects (React, React Native)
  flutter-physical   EdgeInsets.only(left:), Alignment.centerLeft, Positioned(left:) ...
  html-dir           <html> without dir="rtl" / lang="ar..."
  letter-spacing     letter-spacing / tracking-* (breaks Arabic joining in several renderers)
  italic             font-style: italic / italic class on Arabic text (synthetic slant)
  icon-mirror        directional icon (arrow, chevron, send ...) without RTL mirroring
  ltr-input          tel / email / url input without dir="ltr"
  arrow-char         → or ← inside Arabic text (points the wrong way in RTL)

Silence a finding by putting "rtl-ok" in a comment on the same line.

Exit codes: 0 = no errors (warnings allowed), 1 = errors found
(or warnings with --strict), 2 = bad usage.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict

EXTS = {".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".jsx", ".ts",
        ".tsx", ".vue", ".svelte", ".astro", ".mdx", ".dart", ".php", ".erb",
        ".njk", ".hbs", ".liquid", ".jinja", ".j2", ".twig"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", ".nuxt", "out",
             "vendor", "coverage", ".dart_tool", ".svelte-kit", "__pycache__", "Pods"}
CSS_EXTS = {".css", ".scss", ".sass", ".less"}
JS_EXTS = {".js", ".jsx", ".ts", ".tsx", ".mdx"}
MARKUP_EXTS = {".html", ".htm", ".vue", ".svelte", ".astro", ".php", ".erb", ".njk",
               ".hbs", ".liquid", ".jinja", ".j2", ".twig"}

ARABIC = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")


@dataclass
class Finding:
    file: str
    line: int
    col: int
    rule: str
    severity: str  # "error" | "warning"
    message: str
    fix: str


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CSS_PROP_FIX = {
    "margin-left": "margin-inline-start", "margin-right": "margin-inline-end",
    "padding-left": "padding-inline-start", "padding-right": "padding-inline-end",
    "border-left": "border-inline-start", "border-right": "border-inline-end",
    "border-left-width": "border-inline-start-width", "border-right-width": "border-inline-end-width",
    "border-left-color": "border-inline-start-color", "border-right-color": "border-inline-end-color",
    "border-left-style": "border-inline-start-style", "border-right-style": "border-inline-end-style",
    "border-top-left-radius": "border-start-start-radius",
    "border-top-right-radius": "border-start-end-radius",
    "border-bottom-left-radius": "border-end-start-radius",
    "border-bottom-right-radius": "border-end-end-radius",
    "scroll-margin-left": "scroll-margin-inline-start", "scroll-margin-right": "scroll-margin-inline-end",
    "scroll-padding-left": "scroll-padding-inline-start", "scroll-padding-right": "scroll-padding-inline-end",
}
RE_CSS_PROP = re.compile(r"(?<![\w-])(" + "|".join(sorted(map(re.escape, CSS_PROP_FIX), key=len, reverse=True)) + r")\s*:")
RE_CSS_OFFSET = re.compile(r"(?<![\w-])(left|right)\s*:\s*(?!\s*(?:auto\b|inherit\b|initial\b|unset\b))([-\d.]|calc|var|min|max|clamp)")
RE_CSS_VALUE = re.compile(r"(?<![\w-])(text-align|float|clear)\s*:\s*(left|right)\b")
RE_CSS_LETTER = re.compile(r"(?<![\w-])letter-spacing\s*:\s*(?!\s*(?:0(?:\.0+)?(?:px|em|rem)?\s*[;}\"']|0\s*$|normal\b|inherit\b|initial\b|unset\b))")
RE_CSS_ITALIC = re.compile(r"(?<![\w-])font-style\s*:\s*(italic|oblique)\b")
RE_MARGIN_SHORTHAND_SIDE = None  # shorthand values (margin: 0 1rem 0 2rem) are not flagged

# ---------------------------------------------------------------------------
# Tailwind
# ---------------------------------------------------------------------------

TW_VALUE = r"(?:-?\d+(?:\.\d+)?|px|auto|full|\d+/\d+|\[[^\]\s]+\]|\([^)\s]+\))"
TW_SPACING = {"ml": "ms", "mr": "me", "pl": "ps", "pr": "pe", "left": "start", "right": "end",
              "scroll-ml": "scroll-ms", "scroll-mr": "scroll-me",
              "scroll-pl": "scroll-ps", "scroll-pr": "scroll-pe"}
TW_ROUNDED = {"rounded-l": "rounded-s", "rounded-r": "rounded-e", "rounded-tl": "rounded-ss",
              "rounded-tr": "rounded-se", "rounded-bl": "rounded-es", "rounded-br": "rounded-ee"}
TW_BORDER = {"border-l": "border-s", "border-r": "border-e"}
TW_EXACT = {"text-left": "text-start", "text-right": "text-end",
            "float-left": "float-start", "float-right": "float-end",
            "clear-left": "clear-start", "clear-right": "clear-end"}
B = r"(?:(?<=^)|(?<=[\s\"'`{(,]))"           # token start
E = r"(?=$|[\s\"'`},);])"                     # token end
VARIANTS = r"((?:[\w\-\[\]&=:.@/]+?:)*)"     # md:, hover:, group-hover:, [&>*]:
RE_TW_SPACING = re.compile(B + VARIANTS + r"(!?-?)(" + "|".join(sorted(map(re.escape, TW_SPACING), key=len, reverse=True)) + r")-(" + TW_VALUE + r")" + E)
RE_TW_ROUNDED = re.compile(B + VARIANTS + r"(!?)(" + "|".join(sorted(map(re.escape, TW_ROUNDED), key=len, reverse=True)) + r")((?:-[\w\[\]./]+)?)" + E)
RE_TW_BORDER = re.compile(B + VARIANTS + r"(!?)(border-[lr])((?:-(?:\d+|\[[^\]\s]+\]|[a-z]+(?:-\d+)?))?)" + E)
RE_TW_EXACT = re.compile(B + VARIANTS + r"(!?)(" + "|".join(map(re.escape, TW_EXACT)) + r")" + E)
RE_TW_TRACKING = re.compile(B + VARIANTS + r"(!?)(tracking-(?:tighter|tight|wide|wider|widest|\[[^\]\s]+\]|\d+))" + E)
RE_TW_ITALIC = re.compile(B + VARIANTS + r"(italic)" + E)
CLASS_CONTEXT = re.compile(r"\b(class|className|class:list|:class|tw|clsx|cn|cva|twMerge|classNames|classList)\b|@apply")

# ---------------------------------------------------------------------------
# JS style objects (React inline styles, React Native StyleSheet)
# ---------------------------------------------------------------------------

JS_STYLE_FIX_WEB = {
    "marginLeft": "marginInlineStart", "marginRight": "marginInlineEnd",
    "paddingLeft": "paddingInlineStart", "paddingRight": "paddingInlineEnd",
    "borderLeftWidth": "borderInlineStartWidth", "borderRightWidth": "borderInlineEndWidth",
    "borderLeft": "borderInlineStart", "borderRight": "borderInlineEnd",
    "borderTopLeftRadius": "borderStartStartRadius", "borderTopRightRadius": "borderStartEndRadius",
    "borderBottomLeftRadius": "borderEndStartRadius", "borderBottomRightRadius": "borderEndEndRadius",
}
JS_STYLE_FIX_RN = {
    "marginLeft": "marginStart", "marginRight": "marginEnd",
    "paddingLeft": "paddingStart", "paddingRight": "paddingEnd",
    "borderLeftWidth": "borderStartWidth", "borderRightWidth": "borderEndWidth",
    "borderLeftColor": "borderStartColor", "borderRightColor": "borderEndColor",
    "borderTopLeftRadius": "borderTopStartRadius", "borderTopRightRadius": "borderTopEndRadius",
    "borderBottomLeftRadius": "borderBottomStartRadius", "borderBottomRightRadius": "borderBottomEndRadius",
}
RE_JS_STYLE = re.compile(r"(?<![\w$.])(" + "|".join(sorted(set(JS_STYLE_FIX_WEB) | set(JS_STYLE_FIX_RN), key=len, reverse=True)) + r")\s*:")
RE_JS_TEXTALIGN = re.compile(r"(?<![\w$])textAlign\s*:\s*(['\"])(left|right)\1")
RE_RN_OFFSET = re.compile(r"(?<![\w$.])(left|right)\s*:\s*[-\d]")

# ---------------------------------------------------------------------------
# Flutter
# ---------------------------------------------------------------------------

FLUTTER_RULES = [
    (re.compile(r"\bEdgeInsets\.only\(([^)]*\b(?:left|right)\s*:)"), "EdgeInsets.only(left/right:) doesn't flip in RTL",
     "EdgeInsetsDirectional.only(start: ..., end: ...)"),
    (re.compile(r"\bEdgeInsets\.fromLTRB\("), "EdgeInsets.fromLTRB doesn't flip in RTL",
     "EdgeInsetsDirectional.fromSTEB(start, top, end, bottom)"),
    (re.compile(r"\bAlignment\.(topLeft|centerLeft|bottomLeft|topRight|centerRight|bottomRight)\b"),
     "Alignment.{0} doesn't flip in RTL", "AlignmentDirectional.{1}"),
    (re.compile(r"(?<![\w.])Positioned\(([^)]*\b(?:left|right)\s*:)"), "Positioned(left/right:) doesn't flip in RTL",
     "PositionedDirectional(start: ..., end: ...)"),
    (re.compile(r"\bTextAlign\.(left|right)\b"), "TextAlign.{0} doesn't flip in RTL", "TextAlign.{1}"),
    (re.compile(r"\bBorderRadius\.only\(([^)]*\b(?:topLeft|topRight|bottomLeft|bottomRight)\s*:)"),
     "BorderRadius.only(topLeft...) doesn't flip in RTL",
     "BorderRadiusDirectional.only(topStart: ..., topEnd: ...)"),
    (re.compile(r"\bBorder\(([^)]*\b(?:left|right)\s*:)"), "Border(left/right:) doesn't flip in RTL",
     "BorderDirectional(start: ..., end: ...)"),
]
FLUTTER_ALIGN_MAP = {"topLeft": "topStart", "centerLeft": "centerStart", "bottomLeft": "bottomStart",
                     "topRight": "topEnd", "centerRight": "centerEnd", "bottomRight": "bottomEnd"}

# ---------------------------------------------------------------------------
# Icons and inputs
# ---------------------------------------------------------------------------

# Icon components / icon-font classes (always an icon when they appear in markup)
ICON_COMPONENT = re.compile(
    r"(?<![\w-])("
    r"(?:Fi|Fa|Md|Io|Io5|Hi|Hi2|Bi|Ri|Lu|Tb|Pi|Bs|Ai|Gr|Cg)?(?:Arrow|Chevron|Caret|Angle|DoubleArrow)s?(?:Narrow|Long|Small|Big|Circle)?(?:Left|Right|Back|Forward)\w*|"
    r"(?:Send|PaperPlane|Reply|ReplyAll|Undo|Redo|ExternalLink|LogOut|LogIn|SignOut|SignIn|Exit)(?:Icon|Outlined|Rounded|Sharp|2)?|"
    r"fa-(?:arrow|chevron|caret|angle|angles|long-arrow)-(?:left|right)|"
    r"fa-(?:paper-plane|reply|share|right-from-bracket|right-to-bracket|sign-out|sign-in|arrow-right-from-bracket)|"
    r"bi-(?:arrow|chevron|caret|reply|send)[\w-]*|"
    r"(?:lucide|heroicons|ph|mdi|tabler|ri|bx|iconoir)[:-](?:arrow|chevron|caret)[\w-]*(?:left|right|back|forward)[\w-]*|"
    r"(?:arrow|chevron|caret)-(?:left|right|back|forward)(?:-ios|-new|-sharp|-outline|-circle)*"
    r")(?![\w-])")
# Material Symbols / Icons ligature names (only inside an icon element)
ICON_LIGATURE = re.compile(
    r"(?<![\w-])(arrow_back(?:_ios(?:_new)?)?|arrow_forward(?:_ios)?|chevron_left|chevron_right|"
    r"navigate_before|navigate_next|keyboard_arrow_left|keyboard_arrow_right|keyboard_backspace|"
    r"send|reply|reply_all|logout|login|first_page|last_page|redo|undo|trending_flat|east|west)(?![\w-])")
ICON_LIGATURE_CONTEXT = re.compile(r"material|symbol|mat-icon|<Icon\b|<v-icon|<q-icon", re.I)
MIRROR_HINT = re.compile(
    r"rtl:(?:-?scale-x|rotate|-rotate|transform|-?scale)|scale-x-\[-1\]|-scale-x-100|rtl-flip|flip-rtl|"
    r"mirror|scaleX\(-1\)|scale\(-1|rotate-180|\[dir=.?rtl.?\]|dir=.?rtl.?.*\b(?:flip|rotate)|"
    r"isRTL|I18nManager|textDirection|matchTextDirection|useDirection|getDirection|dir\s*===|rtl\s*\?|"
    r"directional-icon|icon-flip|fa-flip-horizontal|flip=\{?[\"']?horizontal|transform:\s*scaleX")
# Flutter's material Icons.arrow_back etc. mirror automatically (matchTextDirection).
FLUTTER_ICON = re.compile(r"\bIcons\.\w+")

RE_INPUT = re.compile(r"<(input|Input|TextField|TextInput|el-input|v-text-field)\b[^>]*>", re.S)
RE_INPUT_TYPE = re.compile(r"""\btype\s*=\s*\{?\s*["'](tel|email|url)["']""")
RE_INPUT_HINT = re.compile(r"""\b(?:autoComplete|autocomplete|name|id|inputMode|inputmode)\s*=\s*\{?\s*["'](?:tel|email|url|phone|mobile|tel-national|username)["']""")
RE_DIR_LTR = re.compile(r"""\bdir\s*=\s*\{?\s*["']ltr["']|direction\s*:\s*["']?ltr|\[direction:ltr\]|\bltr\b""")

RE_HTML_TAG = re.compile(r"<html\b[^>]*>", re.S | re.I)
RE_ATTR_DIR = re.compile(r"""\bdir\s*=\s*\{?\s*["']?(\w+)""", re.I)
RE_ATTR_LANG = re.compile(r"""\blang\s*=\s*\{?\s*["']?([\w-]+)""", re.I)
RE_ATTR_DYNAMIC = re.compile(r"""\b(dir|lang)\s*=\s*\{(?!\s*["'])""")


# ---------------------------------------------------------------------------

def iter_files(paths):
    for p in paths:
        if os.path.isfile(p):
            yield p
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
                for f in sorted(files):
                    if os.path.splitext(f)[1].lower() in EXTS and ".min." not in f:
                        yield os.path.join(root, f)


def line_col(text, idx):
    line = text.count("\n", 0, idx) + 1
    col = idx - (text.rfind("\n", 0, idx) + 1) + 1
    return line, col


def check_file(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as e:
        return [Finding(path, 0, 0, "io", "error", str(e), "")]
    ext = os.path.splitext(path)[1].lower()
    findings = []
    lines = text.split("\n")
    has_arabic = bool(ARABIC.search(text))
    is_rn = "react-native" in text
    in_style_block = False
    in_block_comment = False

    def add(lineno, col, rule, sev, msg, fix):
        src = lines[lineno - 1] if 0 < lineno <= len(lines) else ""
        if "rtl-ok" in src:
            return
        findings.append(Finding(path, lineno, col, rule, sev, msg, fix))

    for n, raw in enumerate(lines, 1):
        line = raw
        # crude comment stripping so commented-out code isn't flagged
        if in_block_comment:
            if "*/" in line:
                line = " " * (line.index("*/") + 2) + line[line.index("*/") + 2:]
                in_block_comment = False
            else:
                continue
        if "/*" in line and "*/" not in line[line.index("/*"):]:
            line = line[: line.index("/*")]
            in_block_comment = True
        line = re.sub(r"/\*.*?\*/", lambda m: " " * len(m.group()), line)
        if ext in JS_EXTS or ext == ".dart":
            line = re.sub(r"(^|[^:\"'`])//.*$", r"\1", line)

        low = line.lower()
        if ext in MARKUP_EXTS:
            if "<style" in low:
                in_style_block = True
            if "</style" in low:
                in_style_block = False if low.rfind("</style") > low.rfind("<style") else True

        css_context = (ext in CSS_EXTS or in_style_block or "<style" in low
                       or re.search(r"\bstyle\s*=\s*[\"']", line)
                       or (ext in JS_EXTS and re.search(r"\b(?:styled|css|createGlobalStyle|keyframes)\b.*`|^\s*[\w-]+\s*:\s*[^:]*;\s*$", line)))
        # hyphenated CSS properties are unambiguous anywhere
        for m in RE_CSS_PROP.finditer(line):
            add(n, m.start() + 1, "physical-css", "error",
                f"`{m.group(1)}` doesn't flip in RTL", f"{CSS_PROP_FIX[m.group(1)]}:")
        for m in RE_CSS_VALUE.finditer(line):
            prop, val = m.group(1), m.group(2)
            fixval = "start" if val == "left" else "end"
            fix = f"{prop}: {fixval}" if prop == "text-align" else f"{prop}: inline-{fixval}"
            add(n, m.start() + 1, "physical-css", "error", f"`{prop}: {val}` doesn't flip in RTL", fix)
        if css_context:
            for m in RE_CSS_OFFSET.finditer(line):
                side = m.group(1)
                add(n, m.start() + 1, "physical-css", "error", f"`{side}:` doesn't flip in RTL",
                    "inset-inline-start:" if side == "left" else "inset-inline-end:")
            for m in RE_CSS_LETTER.finditer(line):
                add(n, m.start() + 1, "letter-spacing", "warning",
                    "letter-spacing breaks Arabic letter joining in several renderers",
                    "remove it, or scope it to Latin text: :lang(en) { letter-spacing: ... }")
            for m in RE_CSS_ITALIC.finditer(line):
                if has_arabic or ext in CSS_EXTS:
                    add(n, m.start() + 1, "italic", "warning",
                        "Arabic fonts have no italic; browsers draw a synthetic slant",
                        "use font-weight or color for emphasis on Arabic; scope italic to :lang(en)")

        # Tailwind (only in class-like contexts, or anywhere in markup/JSX files on class lines)
        if (ext in MARKUP_EXTS or ext in JS_EXTS) and CLASS_CONTEXT.search(line) or (ext in CSS_EXTS and "@apply" in line):
            for m in RE_TW_SPACING.finditer(line):
                variants, neg, util, val = m.groups()
                if re.search(r"(?:^|:)(?:rtl|ltr)(?::|$)", variants or ""):
                    continue
                fix = f"{variants}{neg}{TW_SPACING[util]}-{val}"
                add(n, m.start() + 1, "physical-tailwind", "error",
                    f"`{m.group(0)}` doesn't flip in RTL", fix)
            for m in RE_TW_ROUNDED.finditer(line):
                variants, imp, util, rest = m.groups()
                if re.search(r"(?:^|:)(?:rtl|ltr)(?::|$)", variants or ""):
                    continue
                add(n, m.start() + 1, "physical-tailwind", "error",
                    f"`{m.group(0)}` doesn't flip in RTL", f"{variants}{imp}{TW_ROUNDED[util]}{rest}")
            for m in RE_TW_BORDER.finditer(line):
                variants, imp, util, rest = m.groups()
                if re.search(r"(?:^|:)(?:rtl|ltr)(?::|$)", variants or ""):
                    continue
                add(n, m.start() + 1, "physical-tailwind", "error",
                    f"`{m.group(0)}` doesn't flip in RTL", f"{variants}{imp}{TW_BORDER[util]}{rest}")
            for m in RE_TW_EXACT.finditer(line):
                variants, imp, util = m.groups()
                if re.search(r"(?:^|:)(?:rtl|ltr)(?::|$)", variants or ""):
                    continue
                add(n, m.start() + 1, "physical-tailwind", "error",
                    f"`{m.group(0)}` doesn't flip in RTL", f"{variants}{imp}{TW_EXACT[util]}")
            if has_arabic or ext in CSS_EXTS:
                for m in RE_TW_TRACKING.finditer(line):
                    if "ltr:" in (m.group(1) or "") or "lang-en" in (m.group(1) or ""):
                        continue
                    add(n, m.start() + 1, "letter-spacing", "warning",
                        f"`{m.group(0)}` changes letter-spacing, which breaks Arabic joining in several renderers",
                        "remove it on Arabic text (keep it only on Latin text, e.g. ltr:" + m.group(3) + ")")
                if has_arabic:
                    for m in RE_TW_ITALIC.finditer(line):
                        if "ltr:" in (m.group(1) or ""):
                            continue
                        add(n, m.start() + 1, "italic", "warning",
                            "`italic` on Arabic text draws a synthetic slant",
                            "use font-semibold or a color for emphasis")

        # JS style objects
        if ext in JS_EXTS:
            fixes = JS_STYLE_FIX_RN if is_rn else JS_STYLE_FIX_WEB
            for m in RE_JS_STYLE.finditer(line):
                key = m.group(1)
                if key not in fixes:
                    continue
                note = " (React Native swaps left/right in RTL by default, but start/end is explicit and also works on react-native-web)" if is_rn else ""
                add(n, m.start() + 1, "physical-style", "warning" if is_rn else "error",
                    f"`{key}` doesn't flip in RTL{note}", f"{fixes[key]}:")
            for m in RE_JS_TEXTALIGN.finditer(line):
                fix = "'auto' (or omit)" if is_rn else ("'start'" if m.group(2) == "left" else "'end'")
                add(n, m.start() + 1, "physical-style", "warning" if is_rn else "error",
                    f"`textAlign: '{m.group(2)}'` doesn't follow text direction", f"textAlign: {fix}")
            if is_rn:
                for m in RE_RN_OFFSET.finditer(line):
                    add(n, m.start() + 1, "physical-style", "warning",
                        f"`{m.group(1)}:` is physical", "start:" if m.group(1) == "left" else "end:")

        # Flutter
        if ext == ".dart":
            for rx, msg, fix in FLUTTER_RULES:
                for m in rx.finditer(line):
                    g = m.group(1) if m.groups() else ""
                    if "Alignment." in m.group(0):
                        msg2, fix2 = msg.format(g), fix.format(g, FLUTTER_ALIGN_MAP[g])
                    elif "TextAlign." in m.group(0):
                        msg2, fix2 = msg.format(g), fix.format(g, "start" if g == "left" else "end")
                    else:
                        msg2, fix2 = msg, fix
                    add(n, m.start() + 1, "flutter-physical", "error", msg2, fix2)

        # icons
        if ext != ".dart" and ext not in CSS_EXTS:
            context = " ".join(lines[max(0, n - 2): n + 1])
            hits = []
            if not (line.lstrip().startswith("import") or re.search(r"\bfrom\s+['\"]|require\(", line)):
                if re.search(r"<|class|icon|Icon", line):
                    hits += list(ICON_COMPONENT.finditer(line))
                if ICON_LIGATURE_CONTEXT.search(context):
                    hits += list(ICON_LIGATURE.finditer(line))
            for m in hits:
                name = m.group(1)
                if MIRROR_HINT.search(context):
                    continue
                add(n, m.start() + 1, "icon-mirror", "warning",
                    f"directional icon `{name}` is not mirrored for RTL",
                    'add class "rtl:-scale-x-100" (Tailwind) or CSS [dir="rtl"] .icon { transform: scaleX(-1); } '
                    "or swap Left/Right icons when RTL")

        # arrows in Arabic text
        if ARABIC.search(line):
            for m in re.finditer(r"[→⟶➜➔➡]", line):
                add(n, m.start() + 1, "arrow-char", "warning",
                    "`→` points backwards in Arabic (RTL reads right to left)", "use ← for 'next / continue'")

    # multi-line constructs: <html>, inputs
    if ext in MARKUP_EXTS or ext in JS_EXTS:
        for m in RE_HTML_TAG.finditer(text):
            tag = m.group(0)
            ln, col = line_col(text, m.start())
            dynamic = {x.group(1) for x in RE_ATTR_DYNAMIC.finditer(tag)}
            d = RE_ATTR_DIR.search(tag)
            lang = RE_ATTR_LANG.search(tag)
            if not d and "dir" not in dynamic:
                add(ln, col, "html-dir", "error", "<html> has no dir attribute",
                    '<html lang="ar" dir="rtl">')
            elif d and d.group(1).lower() == "ltr" and lang and lang.group(1).lower().startswith("ar"):
                add(ln, col, "html-dir", "error", '<html lang="ar"> with dir="ltr"', 'dir="rtl"')
            if not lang and "lang" not in dynamic:
                add(ln, col, "html-dir", "error", "<html> has no lang attribute",
                    'lang="ar" (or ar-SA, ar-EG ...): picks Arabic fonts, hyphenation, screen-reader voice')
        for m in RE_INPUT.finditer(text):
            tag = m.group(0)
            t = RE_INPUT_TYPE.search(tag)
            hint = RE_INPUT_HINT.search(tag)
            if is_rn and m.group(1) == "TextInput":
                continue
            if (t or hint) and not RE_DIR_LTR.search(tag):
                ln, col = line_col(text, m.start())
                kind = t.group(1) if t else "phone/email"
                add(ln, col, "ltr-input", "error",
                    f"{kind} input without dir=\"ltr\": digits, + and @ get reordered in RTL",
                    'add dir="ltr" (keep text-align: end / text-right so it lines up with the RTL form)')

    findings.sort(key=lambda f: (f.line, f.col))
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description="Lint code for RTL (Arabic) bugs.")
    ap.add_argument("paths", nargs="+", help="files or folders")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--strict", action="store_true", help="warnings also fail (exit 1)")
    args = ap.parse_args(argv)

    missing = [p for p in args.paths if not os.path.exists(p)]
    if missing:
        print(f"rtl_check: not found: {', '.join(missing)}", file=sys.stderr)
        return 2

    findings, nfiles = [], 0
    for f in iter_files(args.paths):
        nfiles += 1
        findings.extend(check_file(f))

    errors = sum(1 for f in findings if f.severity == "error")
    warnings = len(findings) - errors
    if args.json:
        print(json.dumps({"files": nfiles, "errors": errors, "warnings": warnings,
                          "findings": [asdict(f) for f in findings]}, ensure_ascii=False, indent=2))
    else:
        use_color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
        red, yellow, dim, reset = ("\033[31m", "\033[33m", "\033[2m", "\033[0m") if use_color else ("",) * 4
        for f in findings:
            c = red if f.severity == "error" else yellow
            print(f"{f.file}:{f.line}:{f.col}  {c}{f.severity}{reset} [{f.rule}] {f.message}")
            if f.fix:
                print(f"    {dim}fix:{reset} {f.fix}")
        status = "no RTL problems found" if not findings else f"{errors} error(s), {warnings} warning(s)"
        print(f"\nrtl_check: {nfiles} file(s) scanned, {status}")
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
