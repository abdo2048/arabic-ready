import { chromium } from "playwright";
const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
const p = await b.newPage();
await p.setContent(`<html dir="rtl" lang="ar"><body style="font-size:20px">
<p id=g>أضف الخيار --verbose للتفاصيل</p><p id=h>استخدم الأمر <code dir=ltr>--verbose</code> للتفاصيل</p><p id=k>اتصل على &#x2066;+966 50 123 4567&#x2069;.</p><p id=a>نشر John Smith 3 منشورات</p><p id=b>نشر <bdi>John Smith</bdi> 3 منشورات</p>
<p id=c>درجة الحرارة -5 درجات</p><p id=d>درجة الحرارة &lrm;-5 درجات</p>
<p id=e>اتصل على +966 50 123 4567.</p><p id=f>اتصل على <bdi dir=ltr>+966 50 123 4567</bdi>.</p></body></html>`);
const xs = await p.evaluate(() => {
  const pos = (id, ch, nth = 0) => {           // x of the nth occurrence of ch inside element id
    const el = document.getElementById(id); const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let n, k = 0; while ((n = w.nextNode())) { let i = -1;
      while ((i = n.data.indexOf(ch, i + 1)) >= 0) { if (k++ === nth) { const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + ch.length); return Math.round(r.getBoundingClientRect().x); } } }
  };
  return { phone_LRI_plus_vs_4567: [pos("k","+"), pos("k","4567")], code_raw_dash_vs_save: [pos("g","--"), pos("g","verbose")], code_ltr_dash_vs_save: [pos("h","--"), pos("h","verbose")], raw_3_vs_J: [pos("a", "3"), pos("a", "J")], bdi_3_vs_J: [pos("b", "3"), pos("b", "J")],
    neg_raw_minus_vs_5: [pos("c", "-"), pos("c", "5")], neg_lrm_minus_vs_5: [pos("d", "-"), pos("d", "5")],
    phone_raw_plus_vs_4567: [pos("e", "+"), pos("e", "4567")], phone_bdi_plus_vs_4567: [pos("f", "+"), pos("f", "4567")] };
});
console.log(JSON.stringify(xs, null, 1)); await b.close();
