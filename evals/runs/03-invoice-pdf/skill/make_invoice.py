"""Generate an Arabic RTL invoice PDF (invoice.pdf) with WeasyPrint."""
from decimal import Decimal, ROUND_HALF_UP
from html import escape
from pathlib import Path
import weasyprint

FONT_DIR = Path("/root/.fonts")
VAT_RATE = Decimal("0.05")

seller = {"name": "مؤسسة النور للتجارة", "city": "دبي، الإمارات العربية المتحدة",
          "trn": "100234567800003", "phone": "+971 4 555 0199", "email": "sales@alnoor-trading.ae"}
customer = {"name": "Acme Trading LLC", "phone": "+971 50 123 4567", "email": "billing@acme.ae"}
invoice = {"number": "INV-2026-0147", "date": "18 أكتوبر 2026", "due": "17 نوفمبر 2026"}

items = [  # (description, is_english, qty, unit price AED)
    ("Logitech MX Keys Keyboard", True, 5, Decimal("420.00")),
    ("طاولة مكتب خشبية", False, 3, Decimal("1250.00")),
    ("Dell P2723D Monitor", True, 4, Decimal("1150.00")),
    ("كرسي مكتب مريح", False, 6, Decimal("875.00")),
]

def money(x: Decimal) -> str:
    return f"{x.quantize(Decimal('0.01'), ROUND_HALF_UP):,.2f}"

def ltr(s: str) -> str:
    return f'<bdi dir="ltr">{escape(s)}</bdi>'

rows, subtotal = [], Decimal("0")
for i, (desc, en, qty, price) in enumerate(items, 1):
    line = price * qty
    subtotal += line
    name = ltr(desc) if en else escape(desc)
    rows.append(f"<tr><td class='num'>{i}</td><td class='desc'>{name}</td>"
                f"<td class='num'>{qty}</td><td class='num'>{money(price)}</td>"
                f"<td class='num'>{money(line)}</td></tr>")
vat = (subtotal * VAT_RATE).quantize(Decimal("0.01"), ROUND_HALF_UP)
total = subtotal + vat

html = f"""<!doctype html>
<html lang="ar-AE" dir="rtl"><head><meta charset="utf-8">
<style>
@font-face {{ font-family: "Plex Arabic"; font-weight: 400; src: url("{(FONT_DIR/'IBMPlexSansArabic-400.ttf').as_uri()}"); }}
@font-face {{ font-family: "Plex Arabic"; font-weight: 700; src: url("{(FONT_DIR/'IBMPlexSansArabic-700.ttf').as_uri()}"); }}
@page {{ size: A4; margin: 16mm 16mm 18mm;
  @bottom-center {{ content: "شكرًا لتعاملكم معنا"; font-family: "Plex Arabic"; font-size: 9pt; color: #6b7280; }} }}
:root {{ --ink: #1f2937; --muted: #6b7280; --accent: #0f766e; --line: #e5e7eb; --soft: #f0fdfa; }}
body {{ font-family: "Plex Arabic", "Noto Sans Arabic", sans-serif; color: var(--ink);
  font-size: 10.5pt; line-height: 1.7; background: #fff; margin: 0; }}
header {{ display: flex; justify-content: space-between; align-items: flex-start;
  border-bottom: 3px solid var(--accent); padding-bottom: 10pt; margin-bottom: 14pt; }}
.seller-name {{ font-size: 17pt; font-weight: 700; color: var(--accent); margin: 0; line-height: 1.6; }}
.muted {{ color: var(--muted); font-size: 9.5pt; }}
.title {{ text-align: end; }}
.title h1 {{ font-size: 24pt; margin: 0; line-height: 1.5; }}
.meta {{ border-collapse: collapse; margin-inline-start: auto; font-size: 9.5pt; }}
.meta td {{ padding: 1pt 0; }} .meta td:first-child {{ color: var(--muted); padding-inline-end: 10pt; }}
.parties {{ display: flex; gap: 14pt; margin-bottom: 16pt; }}
.box {{ flex: 1; background: var(--soft); border-radius: 6pt; padding: 8pt 12pt; }}
.box h2 {{ font-size: 10pt; color: var(--accent); margin: 0 0 2pt; }}
.box .name {{ font-weight: 700; font-size: 12pt; }}
table.items {{ width: 100%; border-collapse: collapse; }}
table.items th {{ background: var(--accent); color: #fff; font-weight: 700; padding: 6pt 8pt; text-align: start; }}
table.items td {{ padding: 6pt 8pt; border-bottom: 1px solid var(--line); }}
table.items tr:nth-child(even) td {{ background: #f9fafb; }}
.num {{ text-align: center; white-space: nowrap; }}
th.num {{ text-align: center; }}
.totals {{ width: 46%; margin-inline-start: auto; margin-top: 12pt; border-collapse: collapse; }}
.totals td {{ padding: 5pt 8pt; }} .totals td:last-child {{ text-align: end; white-space: nowrap; }}
.totals tr.grand td {{ background: var(--accent); color: #fff; font-weight: 700; font-size: 12pt; }}
.notes {{ margin-top: 22pt; font-size: 9.5pt; color: var(--muted); }}
</style></head><body>
<header>
  <div>
    <p class="seller-name">{seller['name']}</p>
    <div class="muted">{seller['city']}</div>
    <div class="muted">الرقم الضريبي: {ltr(seller['trn'])}</div>
    <div class="muted">الهاتف: {ltr(seller['phone'])} · البريد: {ltr(seller['email'])}</div>
  </div>
  <div class="title">
    <h1>فاتورة ضريبية</h1>
    <table class="meta">
      <tr><td>رقم الفاتورة</td><td>{ltr(invoice['number'])}</td></tr>
      <tr><td>تاريخ الإصدار</td><td>{invoice['date']}</td></tr>
      <tr><td>تاريخ الاستحقاق</td><td>{invoice['due']}</td></tr>
    </table>
  </div>
</header>
<section class="parties">
  <div class="box"><h2>فاتورة إلى</h2>
    <div class="name">{ltr(customer['name'])}</div>
    <div>الهاتف: {ltr(customer['phone'])}</div>
    <div>البريد الإلكتروني: {ltr(customer['email'])}</div></div>
  <div class="box"><h2>طريقة الدفع</h2>
    <div>تحويل بنكي خلال 30 يومًا من تاريخ الإصدار</div>
    <div>العملة: درهم إماراتي ({ltr('AED')})</div></div>
</section>
<table class="items">
  <thead><tr><th class="num">#</th><th>الصنف</th><th class="num">الكمية</th>
  <th class="num">سعر الوحدة (درهم)</th><th class="num">الإجمالي (درهم)</th></tr></thead>
  <tbody>{''.join(rows)}</tbody>
</table>
<table class="totals">
  <tr><td>المجموع الفرعي</td><td>{money(subtotal)} درهم</td></tr>
  <tr><td>ضريبة القيمة المضافة ({ltr('5%')})</td><td>{money(vat)} درهم</td></tr>
  <tr class="grand"><td>الإجمالي المستحق</td><td>{money(total)} درهم</td></tr>
</table>
<p class="notes">جميع الأسعار بالدرهم الإماراتي ({ltr('AED')}). يُرجى ذكر رقم الفاتورة عند التحويل.</p>
</body></html>"""

Path("invoice.html").write_text(html, encoding="utf-8")
weasyprint.HTML(string=html, base_url=".").write_pdf("invoice.pdf")
print("subtotal", money(subtotal), "vat", money(vat), "total", money(total))
