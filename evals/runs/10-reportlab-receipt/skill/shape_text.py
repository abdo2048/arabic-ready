#!/usr/bin/env python3
"""Prepare Arabic strings for renderers that do not shape text themselves.

Some renderers draw code points one by one, left to right. Arabic then comes
out as disconnected letters in reversed order. The fix is to (1) replace each
letter with its contextual presentation form and (2) reorder the line into
visual order. Renderers that already shape text (browsers, Word, LibreOffice,
WeasyPrint, matplotlib >= 3.11, Pillow with libraqm, fpdf2 with
set_text_shaping) must get the raw string. Shaping twice reverses it again.

Usage as a module (copy this file next to your script, or add it to sys.path):

    from shape_text import prepare
    label = prepare("المبيعات الشهرية", target="matplotlib")   # no-op on 3.11+
    text  = prepare("فاتورة رقم 1024", target="reportlab")     # always shaped

Command line:

    python shape_text.py --check                    # what this machine needs
    python shape_text.py "نص عربي 123" [--target pillow|matplotlib|reportlab|basic]

Backends, in order of preference:
  1. arabic-reshaper + python-bidi (the reference implementation). If they are
     missing, they are pip-installed on demand, because the Python standard
     library has no Arabic shaping and no complete Unicode Bidi Algorithm.
  2. A built-in standard-library fallback, used when pip is unavailable
     (offline sandboxes). It builds the presentation-form table from
     unicodedata and implements the bidi rules needed for a single line of
     Arabic mixed with Latin, digits and punctuation. It does not handle
     explicit embeddings (LRE/RLE/PDF) or isolates (LRI/RLI/FSI).
"""
from __future__ import annotations

import argparse
import importlib
import subprocess
import sys
import unicodedata

__all__ = ["prepare", "shape", "visual", "needs_shaping", "capabilities"]

# --------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------

def _version_tuple(v: str) -> tuple:
    out = []
    for part in v.split(".")[:3]:
        num = "".join(ch for ch in part if ch.isdigit())
        out.append(int(num) if num else 0)
    return tuple(out)


def capabilities() -> dict:
    """Report which renderers on this machine shape Arabic natively."""
    caps = {}
    try:
        import matplotlib
        caps["matplotlib"] = matplotlib.__version__
        caps["matplotlib_native_shaping"] = _version_tuple(matplotlib.__version__) >= (3, 11)
    except ImportError:
        caps["matplotlib"] = None
    try:
        import PIL
        from PIL import features
        caps["pillow"] = PIL.__version__
        caps["pillow_raqm"] = bool(features.check("raqm"))
    except ImportError:
        caps["pillow"] = None
    try:
        import fpdf
        caps["fpdf2"] = getattr(fpdf, "__version__", "?")
        caps["uharfbuzz"] = importlib.util.find_spec("uharfbuzz") is not None
    except ImportError:
        caps["fpdf2"] = None
    caps["arabic_reshaper"] = importlib.util.find_spec("arabic_reshaper") is not None
    caps["python_bidi"] = importlib.util.find_spec("bidi") is not None
    return caps


def needs_shaping(target: str = "basic") -> bool:
    """True if `target` draws raw code points and needs prepare()."""
    target = target.lower()
    caps = capabilities()
    if target == "matplotlib":
        return not caps.get("matplotlib_native_shaping", False)
    if target == "pillow":
        return not caps.get("pillow_raqm", False)
    # reportlab canvas/Paragraph, PyMuPDF insert_text, OpenCV putText,
    # fpdf2 without set_text_shaping, anything else that draws glyph by glyph
    return True


# --------------------------------------------------------------------------
# Reference backend (arabic-reshaper + python-bidi), installed on demand
# --------------------------------------------------------------------------

_LIBS = None  # (reshape, get_display) or False if unavailable


def _keep_harakat(arabic_reshaper):
    # arabic_reshaper.reshape() deletes tashkeel by default; keep it.
    return arabic_reshaper.ArabicReshaper(configuration={"delete_harakat": False}).reshape


def _load_libs(allow_install: bool = True):
    global _LIBS
    if _LIBS is not None:
        return _LIBS
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        _LIBS = (_keep_harakat(arabic_reshaper), get_display)
        return _LIBS
    except ImportError:
        pass
    if allow_install:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet",
                 "arabic-reshaper", "python-bidi"],
                check=True, timeout=120,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            importlib.invalidate_caches()
            import arabic_reshaper
            from bidi.algorithm import get_display
            _LIBS = (_keep_harakat(arabic_reshaper), get_display)
            return _LIBS
        except Exception:
            pass
    _LIBS = False
    return _LIBS


# --------------------------------------------------------------------------
# Standard-library fallback: shaping
# --------------------------------------------------------------------------

_FORMS: dict = {}       # base char -> {"isolated": c, "final": c, "initial": c, "medial": c}
_LIGATURES: dict = {}   # (lam, alef variant) -> {"isolated": c, "final": c}


def _build_tables():
    if _FORMS:
        return
    for cp in list(range(0xFB50, 0xFE00)) + list(range(0xFE70, 0xFF00)):
        ch = chr(cp)
        dec = unicodedata.decomposition(ch)
        if not dec.startswith("<"):
            continue
        tag, *codes = dec.split()
        form = tag.strip("<>")
        if form not in ("isolated", "final", "initial", "medial"):
            continue
        base = "".join(chr(int(c, 16)) for c in codes)
        if len(base) == 1:
            _FORMS.setdefault(base, {}).setdefault(form, ch)
        elif len(base) == 2 and base[0] == "ل" and base[1] in "آأإا":
            _LIGATURES.setdefault(base, {}).setdefault(form, ch)


def _joining(ch: str) -> str:
    """'D' dual-joining, 'R' right-joining, 'T' transparent, 'C' join-causing, 'U' none."""
    if ch == "ـ" or ch == "‍":            # tatweel, ZWJ
        return "C"
    if unicodedata.category(ch) == "Mn" or ch == "‌":
        return "T" if ch != "‌" else "U"
    forms = _FORMS.get(ch)
    if not forms:
        return "U"
    if "initial" in forms or "medial" in forms:
        return "D"
    if "final" in forms:
        return "R"
    return "U"


def shape(text: str) -> str:
    """Replace Arabic letters with contextual presentation forms (logical order kept)."""
    _build_tables()
    chars = list(text)
    n = len(chars)
    out = []
    i = 0

    def prev_joiner(idx):
        j = idx - 1
        while j >= 0 and _joining(chars[j]) == "T":
            j -= 1
        return _joining(chars[j]) if j >= 0 else "U"

    def next_joiner(idx):
        j = idx + 1
        while j < n and _joining(chars[j]) == "T":
            j += 1
        return (_joining(chars[j]), j) if j < n else ("U", n)

    while i < n:
        ch = chars[i]
        jt = _joining(ch)
        if jt not in ("D", "R"):
            out.append(ch)
            i += 1
            continue
        joins_prev = prev_joiner(i) in ("D", "C")
        # lam + alef ligature
        if ch == "ل":
            nj, nidx = next_joiner(i)
            if nidx < n and (ch + chars[nidx]) in _LIGATURES and all(
                    _joining(c) == "T" for c in chars[i + 1:nidx]):
                lig = _LIGATURES[ch + chars[nidx]]
                out.append(lig["final"] if joins_prev and "final" in lig else lig["isolated"])
                out.extend(chars[i + 1:nidx])   # marks between lam and alef
                i = nidx + 1
                continue
        nxt, _ = next_joiner(i)
        joins_next = jt == "D" and nxt in ("D", "R", "C")
        forms = _FORMS[ch]
        if joins_prev and joins_next:
            form = "medial"
        elif joins_prev:
            form = "final"
        elif joins_next:
            form = "initial"
        else:
            form = "isolated"
        out.append(forms.get(form) or forms.get("isolated") or ch)
        i += 1
    return "".join(out)


# --------------------------------------------------------------------------
# Standard-library fallback: bidi (single paragraph, no explicit embeddings)
# --------------------------------------------------------------------------

_MIRROR = dict(zip("()[]{}<>«»‹›", ")(][}{><»«›‹"))


def _bidi_classes(text: str, base_level: int) -> list:
    types = [unicodedata.bidirectional(c) or "L" for c in text]
    sos = "R" if base_level else "L"
    # W1: NSM takes the type of the previous char
    for i, t in enumerate(types):
        if t == "NSM":
            types[i] = types[i - 1] if i else sos
    # W2: EN after AL becomes AN
    last_strong = sos
    for i, t in enumerate(types):
        if t in ("L", "R", "AL"):
            last_strong = t
        elif t == "EN" and last_strong == "AL":
            types[i] = "AN"
    # W3: AL -> R
    types = ["R" if t == "AL" else t for t in types]
    # W4: single ES/CS between numbers
    for i in range(1, len(types) - 1):
        a, b, c = types[i - 1], types[i], types[i + 1]
        if b == "ES" and a == c == "EN":
            types[i] = "EN"
        elif b == "CS" and a == c and a in ("EN", "AN"):
            types[i] = a
    # W5: ET sequences adjacent to EN become EN
    i = 0
    while i < len(types):
        if types[i] == "ET":
            j = i
            while j < len(types) and types[j] == "ET":
                j += 1
            if (i > 0 and types[i - 1] == "EN") or (j < len(types) and types[j] == "EN"):
                for k in range(i, j):
                    types[k] = "EN"
            i = j
        else:
            i += 1
    # W6: remaining separators/terminators -> ON
    types = ["ON" if t in ("ES", "ET", "CS") else t for t in types]
    # W7: EN preceded by L (or sos L) -> L
    last_strong = sos
    for i, t in enumerate(types):
        if t in ("L", "R"):
            last_strong = t
        elif t == "EN" and last_strong == "L":
            types[i] = "L"
    # N1/N2: neutrals take surrounding strong direction (EN/AN count as R)
    neutral = ("ON", "WS", "S", "B", "BN", "LRE", "RLE", "PDF", "LRO", "RLO",
               "LRI", "RLI", "FSI", "PDI")
    e_dir = "R" if base_level else "L"
    i = 0
    while i < len(types):
        if types[i] in neutral:
            j = i
            while j < len(types) and types[j] in neutral:
                j += 1
            before = sos if i == 0 else ("R" if types[i - 1] in ("R", "EN", "AN") else "L")
            after = sos if j == len(types) else ("R" if types[j] in ("R", "EN", "AN") else "L")
            fill = before if before == after else e_dir
            for k in range(i, j):
                types[k] = fill
            i = j
        else:
            i += 1
    return types


def visual(text: str, base_dir: str = "rtl") -> str:
    """Reorder each line of `text` from logical to visual order."""
    return "\n".join(_visual_line(line, base_dir) for line in text.split("\n"))


def _visual_line(line: str, base_dir: str) -> str:
    if not line:
        return line
    if base_dir == "auto":
        base_dir = "ltr"
        for c in line:
            t = unicodedata.bidirectional(c)
            if t in ("R", "AL"):
                base_dir = "rtl"
                break
            if t == "L":
                break
    base = 1 if base_dir == "rtl" else 0
    types = _bidi_classes(line, base)
    levels = []
    for t in types:
        if base == 0:
            levels.append(1 if t == "R" else 2 if t in ("AN", "EN") else 0)
        else:
            levels.append(2 if t in ("L", "EN", "AN") else 1)
    # L1: trailing whitespace back to paragraph level
    k = len(line) - 1
    while k >= 0 and unicodedata.bidirectional(line[k]) in ("WS", "S", "B", "BN"):
        levels[k] = base
        k -= 1
    # Combining marks share their base's level (rule W1), so in RTL runs they
    # end up before the base in visual order. Glyph-by-glyph renderers expect
    # exactly that (verified with Pillow's BASIC layout).
    units, ulevels = list(line), levels
    # L4: mirror brackets at odd levels
    units = [_MIRROR.get(u, u) if lv % 2 else u for u, lv in zip(units, ulevels)]
    # L2: reverse runs from the highest level down to the lowest odd level
    top = max(ulevels)
    low_odd = min(lv for lv in ulevels if lv % 2) if any(lv % 2 for lv in ulevels) else top + 1
    for lvl in range(top, low_odd - 1, -1):
        i = 0
        while i < len(units):
            if ulevels[i] >= lvl:
                j = i
                while j < len(units) and ulevels[j] >= lvl:
                    j += 1
                units[i:j] = units[i:j][::-1]
                ulevels[i:j] = ulevels[i:j][::-1]
                i = j
            else:
                i += 1
    return "".join(units)


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------

def prepare(text: str, target: str = "basic", base_dir: str = "rtl",
            force: bool = False, allow_install: bool = True) -> str:
    """Return `text` ready for `target`.

    target: "matplotlib", "pillow", "reportlab", "basic" (anything that draws
    glyph by glyph). For matplotlib >= 3.11 and Pillow with libraqm the text
    is returned unchanged, because those shape natively and double shaping
    breaks the output. Pass force=True to shape anyway (e.g. Pillow with
    layout_engine=ImageFont.Layout.BASIC).
    """
    if not force and not needs_shaping(target):
        return text
    libs = _load_libs(allow_install)
    if libs:
        reshape, get_display = libs
        out = []
        for line in text.split("\n"):
            out.append(get_display(reshape(line), base_dir="R" if base_dir == "rtl" else "L"))
        return "\n".join(out)
    return visual(shape(text), base_dir)


def _main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("text", nargs="?", help="Arabic text to prepare")
    ap.add_argument("--target", default="basic",
                    choices=["basic", "matplotlib", "pillow", "reportlab"])
    ap.add_argument("--check", action="store_true", help="report native shaping support")
    ap.add_argument("--fallback", action="store_true",
                    help="use the built-in stdlib shaper even if libraries exist")
    args = ap.parse_args(argv)
    if args.check or not args.text:
        caps = capabilities()
        for k, v in caps.items():
            print(f"{k:28} {v}")
        print()
        for t in ("matplotlib", "pillow", "reportlab"):
            verdict = "pass Arabic through prepare()" if needs_shaping(t) else "use raw text (native shaping)"
            print(f"{t:12} -> {verdict}")
        return 0
    if args.fallback:
        print(visual(shape(args.text)))
    else:
        print(prepare(args.text, target=args.target, force=args.target in ("basic", "reportlab")))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
