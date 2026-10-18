"""Tests for skills/arabic-ready/scripts/shape_text.py (stdlib fallback vs reference libs)."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skills", "arabic-ready", "scripts"))
import shape_text  # noqa: E402
from shape_text import shape, visual, prepare  # noqa: E402

CASES = [
    "فاتورة رقم 1024 للعميل Acme، الإجمالي 49.99 دولار؟",
    "المبيعات الشهرية", "السلام عليكم", "الإيرادات (ألف)", "مرحبا بالعالم!",
    "اتصل على +966 50 123 4567.", "درجة الحرارة -5 درجات", "نشر John Smith 3 منشورات",
    "نسبة النمو 25% في 2026", "البريد: support@acme.com", "٣٫٥ مليون ريال",
    "لأن الألوان [أحمر] و{أزرق}", "كتاب «الأيام» لطه حسين", "آلاف", "Hello عالم world",
    "سؤال: لماذا؟ — جواب.", "الإصدار v2.1.0 متاح", "من 9:00 إلى 17:00",
]


class TestFallbackShaping(unittest.TestCase):
    def test_contextual_forms(self):
        # ب isolated / initial / medial / final
        self.assertEqual(shape("ب"), "ﺏ")
        self.assertEqual(shape("بب"), "ﺑﺐ")
        self.assertEqual(shape("ببب"), "ﺑﺒﺐ")

    def test_right_joining_letter_breaks_chain(self):
        # د joins only to the right: "بدب" -> initial beh, final dal, isolated beh
        self.assertEqual(shape("بدب"), "ﺑﺪﺏ")

    def test_lam_alef_ligature(self):
        self.assertEqual(shape("لا"), "ﻻ")
        self.assertEqual(shape("بلا"), "ﺑﻼ")

    def test_tashkeel_is_transparent(self):
        self.assertEqual(shape("بَب"), "ﺑَﺐ")

    def test_latin_untouched(self):
        self.assertEqual(visual(shape("abc 123"), "ltr"), "abc 123")

    def test_mirrors_brackets_in_rtl(self):
        self.assertEqual(visual("(ب)"), "(ب)")  # reversed AND mirrored -> looks the same

    def test_negative_number_needs_lrm(self):
        # Same result as browsers: a bare "-5" in RTL text shows as "5-" ...
        self.assertIn("5-", visual(shape("درجة -5")))
        # ... and an LRM before the sign fixes it
        self.assertIn("\u200e-5", visual(shape("درجة \u200e-5")))

    def test_matches_reference_implementation(self):
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
        except ImportError:
            self.skipTest("arabic-reshaper / python-bidi not installed")
        reshaper = arabic_reshaper.ArabicReshaper(configuration={"delete_harakat": False})
        for c in CASES:
            with self.subTest(text=c):
                self.assertEqual(visual(shape(c)), get_display(reshaper.reshape(c), base_dir="R"))


class TestCli(unittest.TestCase):
    def test_check_runs_in_fresh_interpreter(self):
        import subprocess
        script = os.path.join(HERE, "..", "skills", "arabic-ready", "scripts", "shape_text.py")
        p = subprocess.run([sys.executable, "-I", script, "--check"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("matplotlib", p.stdout)

    def test_fallback_cli(self):
        import subprocess
        script = os.path.join(HERE, "..", "skills", "arabic-ready", "scripts", "shape_text.py")
        p = subprocess.run([sys.executable, "-I", script, "--fallback", "بب"], capture_output=True, text=True)
        self.assertEqual(p.stdout.strip(), "\uFE90\uFE91")


class TestPrepare(unittest.TestCase):
    def test_force_shapes(self):
        out = prepare("بب", force=True, allow_install=False)
        self.assertEqual(out, "ﺐﺑ")  # visual order: final form first

    def test_native_targets_untouched(self):
        orig = shape_text.needs_shaping
        shape_text.needs_shaping = lambda target="basic": False
        try:
            self.assertEqual(prepare("مرحبا", target="matplotlib"), "مرحبا")
        finally:
            shape_text.needs_shaping = orig

    def test_multiline(self):
        out = prepare("سطر أول\nسطر ثان", force=True, allow_install=False)
        self.assertEqual(len(out.split("\n")), 2)


if __name__ == "__main__":
    unittest.main()
