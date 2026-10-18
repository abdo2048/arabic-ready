"""Tests for skills/arabic-ready/scripts/rtl_check.py. Run: python -m unittest discover tests"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "skills", "arabic-ready", "scripts", "rtl_check.py")
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.dirname(SCRIPT))
import rtl_check  # noqa: E402


def run(*args):
    p = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def check_text(text, ext):
    with tempfile.NamedTemporaryFile("w", suffix=ext, delete=False, encoding="utf-8") as f:
        f.write(text)
    try:
        return rtl_check.check_file(f.name)
    finally:
        os.unlink(f.name)


def fixes(findings):
    return {(f.rule, f.fix) for f in findings}


class TestFixtures(unittest.TestCase):
    def test_good_fixtures_are_clean(self):
        for name in ["good.html", "good.tsx", "rn_good.tsx", "good.dart", "good.css"]:
            with self.subTest(name=name):
                found = rtl_check.check_file(os.path.join(FIX, name))
                self.assertEqual(found, [], "\n".join(f"{f.line}: {f.message}" for f in found))

    def test_bad_html(self):
        found = rtl_check.check_file(os.path.join(FIX, "bad.html"))
        rules = [f.rule for f in found]
        for rule in ["html-dir", "physical-css", "physical-tailwind", "letter-spacing",
                     "italic", "icon-mirror", "ltr-input", "arrow-char"]:
            self.assertIn(rule, rules)
        self.assertIn(("physical-css", "margin-inline-start:"), fixes(found))
        self.assertIn(("physical-css", "inset-inline-start:"), fixes(found))
        self.assertIn(("physical-css", "float: inline-end"), fixes(found))
        self.assertIn(("physical-tailwind", "ms-4"), fixes(found))

    def test_bad_tsx(self):
        found = rtl_check.check_file(os.path.join(FIX, "bad.tsx"))
        f = fixes(found)
        for fix in ["ps-6", "md:me-auto", "rounded-s-lg", "border-e-2", "-ms-1", "start-0", "hover:ms-2"]:
            self.assertIn(("physical-tailwind", fix), f)
        self.assertIn(("physical-style", "marginInlineStart:"), f)
        icons = sorted(x.message.split("`")[1] for x in found if x.rule == "icon-mirror")
        self.assertEqual(icons, ["ArrowLeft", "ChevronRight", "Send"])
        self.assertEqual(sum(1 for x in found if x.rule == "ltr-input"), 2)

    def test_react_native_suggests_start_end(self):
        found = rtl_check.check_file(os.path.join(FIX, "rn_bad.tsx"))
        self.assertIn(("physical-style", "marginStart:"), fixes(found))
        self.assertIn(("physical-style", "end:"), fixes(found))
        self.assertTrue(all(x.severity == "warning" for x in found))

    def test_flutter(self):
        found = rtl_check.check_file(os.path.join(FIX, "bad.dart"))
        f = {x.fix for x in found}
        self.assertIn("AlignmentDirectional.centerStart", f)
        self.assertIn("TextAlign.start", f)
        self.assertIn("EdgeInsetsDirectional.fromSTEB(start, top, end, bottom)", f)
        self.assertIn("PositionedDirectional(start: ..., end: ...)", f)
        # Flutter's Icons.arrow_back mirrors automatically: never flagged
        self.assertFalse(any(x.rule == "icon-mirror" for x in found))


class TestRules(unittest.TestCase):
    def test_rtl_and_ltr_variants_are_intentional(self):
        self.assertEqual(check_text('<div className="rtl:mr-2 ltr:ml-2 rtl:text-right"></div>', ".tsx"), [])

    def test_symmetric_utilities_not_flagged(self):
        self.assertEqual(check_text('<div class="mx-4 px-2 inset-x-0 space-y-2 translate-x-1"></div>', ".html"), [])

    def test_arbitrary_values(self):
        found = check_text('<div class="ml-[13px] pr-[var(--gap)]"></div>', ".html")
        self.assertEqual({x.fix for x in found}, {"ms-[13px]", "pe-[var(--gap)]"})

    def test_important_and_negative(self):
        found = check_text('<div className="!pl-2 -mr-4"></div>', ".jsx")
        self.assertEqual({x.fix for x in found}, {"!ps-2", "-me-4"})

    def test_left_auto_and_shorthand_ok(self):
        self.assertEqual(check_text(".a { left: auto; margin: 0 auto; }", ".css"), [])

    def test_left_in_plain_js_object_not_flagged(self):
        # `left:` outside CSS context (e.g. a chart config) is not a CSS property
        self.assertEqual(check_text("const pos = { left: 10, top: 5 };", ".ts"), [])

    def test_rtl_ok_suppresses(self):
        self.assertEqual(check_text(".a { margin-left: 4px; } /* rtl-ok */", ".css"), [])

    def test_commented_out_code_ignored(self):
        self.assertEqual(check_text("/* .a { margin-left: 4px; } */\n// <div className=\"ml-2\">", ".tsx"), [])

    def test_html_lang_ar_with_ltr(self):
        found = check_text('<html lang="ar" dir="ltr"><body></body></html>', ".html")
        self.assertEqual([x.fix for x in found], ['dir="rtl"'])

    def test_dynamic_dir_accepted(self):
        self.assertEqual(check_text("<html lang={locale} dir={dir}>", ".tsx"), [])

    def test_multiline_input(self):
        found = check_text('<input\n  type="tel"\n  name="phone"\n/>', ".html")
        self.assertEqual([(x.rule, x.line) for x in found], [("ltr-input", 1)])

    def test_tracking_only_flagged_with_arabic(self):
        self.assertEqual(check_text('<h1 class="tracking-wide">Hello</h1>', ".html"), [])
        self.assertEqual(len(check_text('<h1 class="tracking-wide">مرحبا</h1>', ".html")), 1)

    def test_non_directional_icons_not_flagged(self):
        src = '<Play className="a" /><Check className="a" /><Clock className="a" /><span class="material-symbols-outlined">pause</span>'
        self.assertEqual(check_text(src, ".tsx"), [])

    def test_icon_hint_on_neighbouring_line(self):
        src = '<span className="rtl:-scale-x-100 inline-block">\n  <ChevronRight className="size-4" />\n</span>'
        self.assertEqual(check_text(src, ".tsx"), [])

    def test_letter_spacing_zero_ok(self):
        self.assertEqual(check_text(".a { letter-spacing: 0; } .b { letter-spacing: normal; }", ".css"), [])


class TestCli(unittest.TestCase):
    def test_exit_codes(self):
        self.assertEqual(run(os.path.join(FIX, "good.html"))[0], 0)
        self.assertEqual(run(os.path.join(FIX, "bad.css"))[0], 1)
        self.assertEqual(run(os.path.join(FIX, "does-not-exist"))[0], 2)

    def test_warnings_only_exit_0_unless_strict(self):
        path = os.path.join(FIX, "rn_bad.tsx")
        self.assertEqual(run(path)[0], 0)
        self.assertEqual(run(path, "--strict")[0], 1)

    def test_output_format(self):
        code, out, _ = run(os.path.join(FIX, "bad.css"))
        self.assertIn("bad.css:1:8  error [physical-css] `margin-right` doesn't flip in RTL", out)
        self.assertIn("fix: margin-inline-end:", out)
        self.assertIn("6 error(s), 0 warning(s)", out)

    def test_json(self):
        code, out, _ = run(os.path.join(FIX, "bad.css"), "--json")
        data = json.loads(out)
        self.assertEqual(data["errors"], 6)
        self.assertEqual(data["findings"][0]["fix"], "margin-inline-end:")

    def test_folder_scan_skips_node_modules(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "node_modules", "x"))
            with open(os.path.join(d, "node_modules", "x", "a.css"), "w") as f:
                f.write(".a{margin-left:1px}")
            with open(os.path.join(d, "ok.css"), "w") as f:
                f.write(".a{margin-inline-start:1px}")
            code, out, _ = run(d)
            self.assertEqual(code, 0)
            self.assertIn("1 file(s) scanned", out)


if __name__ == "__main__":
    unittest.main()
