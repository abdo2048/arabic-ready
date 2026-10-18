"""Generate an Arabic (RTL) invoice PDF using WeasyPrint (HarfBuzz shaping + bidi)."""
from decimal import Decimal, ROUND_HALF_UP
from weasyprint import HTML

seller = "مؤسسة النور للتجارة"
customer = {"name": "Acme Trading LLC", "phone": "+971 50 123 4567", "email": "billing@acme.ae"}
items = [
    ("Wireless Keyboard", 3, Decimal("120.00")),
    ("حبر طابعة أسود", 5, Decimal("85.50")),
    ("USB-C Hub", 2, Decimal("210.00")),
    ("ورق تصوير A4 (كرتونة)", 10, Decimal("45.00")),
]
VAT = Decimal("0.05")
q = lambda d: d.quantize(Decimal("0.01"), ROUND_HALF_UP)
fmt = lambda d: f"{q(d):,.2f}"

def cell(text):
    # isolate Latin-script values so bidi doesn't reorder them inside RTL cells
    return f'<bdi dir="ltr">{text}</bdi>' if text.isascii() else text

rows, subtotal = [], Decimal(0)
for i, (name, qty, price) in enumerate(items, 1):
    total = qty * price
    subtotal += total
    rows.append(f"<tr><td>{i}</td><td class='name'>{cell(name)}</td><td>{qty}</td>"
                f"<td class='num'>{fmt(price)}</td><td class='num'>{fmt(total)}</td></tr>")
vat = q(subtotal * VAT)
grand = q(subtotal) + vat

html = f"""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 18mm; }}
body {{ font-family: 'IBM Plex Sans Arabic', 'Noto Kufi Arabic', sans-serif; font-size: 11pt; color:#222; }}
.top {{ display:flex; justify-content:space-between; align-items:flex-start; border-bottom:3px solid #1f5f8b; padding-bottom:10px; }}
h1 {{ margin:0; color:#1f5f8b; font-size:26pt; }}
.seller {{ font-size:15pt; font-weight:bold; }}
.meta td {{ padding:2px 0 2px 12px; }}
.box {{ margin:18px 0; padding:10px 14px; background:#f3f7fa; border-radius:6px; }}
.box h3 {{ margin:0 0 6px; font-size:12pt; color:#1f5f8b; }}
table.items {{ width:100%; border-collapse:collapse; margin-top:10px; }}
.items th {{ background:#1f5f8b; color:#fff; padding:8px; text-align:right; }}
.items td {{ padding:8px; border-bottom:1px solid #ddd; }}
.items tr:nth-child(even) td {{ background:#fafafa; }}
.num {{ font-variant-numeric: tabular-nums; }}
.totals {{ width:55%; margin-top:16px; margin-right:auto; border-collapse:collapse; }}
.totals td {{ padding:6px 8px; white-space:nowrap; }} .totals td.num {{ text-align:left; }}
.totals tr.grand td {{ border-top:2px solid #1f5f8b; font-weight:bold; font-size:13pt; color:#1f5f8b; }}
.foot {{ margin-top:40px; font-size:9.5pt; color:#666; text-align:center; }}
</style></head><body>
<div class="top">
  <div><div class="seller">{seller}</div><div>الإمارات العربية المتحدة</div></div>
  <div><h1>فاتورة ضريبية</h1>
    <table class="meta"><tr><td>رقم الفاتورة:</td><td><bdi dir="ltr">INV-2026-0142</bdi></td></tr>
    <tr><td>التاريخ:</td><td><bdi dir="ltr">2026-10-18</bdi></td></tr>
    <tr><td>العملة:</td><td>درهم إماراتي (<bdi dir="ltr">AED</bdi>)</td></tr></table></div>
</div>
<div class="box"><h3>فاتورة إلى</h3>
  <div><bdi dir="ltr">{customer['name']}</bdi></div>
  <div>الهاتف: <bdi dir="ltr">{customer['phone']}</bdi></div>
  <div>البريد الإلكتروني: <bdi dir="ltr">{customer['email']}</bdi></div>
</div>
<table class="items"><thead><tr><th>#</th><th>الصنف</th><th>الكمية</th>
<th>سعر الوحدة (<bdi dir="ltr">AED</bdi>)</th><th>الإجمالي (<bdi dir="ltr">AED</bdi>)</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<table class="totals">
<tr><td>المجموع الفرعي</td><td class="num"><bdi dir="ltr">{fmt(subtotal)} AED</bdi></td></tr>
<tr><td>ضريبة القيمة المضافة (<bdi dir="ltr">5%</bdi>)</td><td class="num"><bdi dir="ltr">{fmt(vat)} AED</bdi></td></tr>
<tr class="grand"><td>الإجمالي المستحق</td><td class="num"><bdi dir="ltr">{fmt(grand)} AED</bdi></td></tr>
</table>
<div class="foot">شكرًا لتعاملكم معنا — {seller}</div>
</body></html>"""

HTML(string=html).write_pdf("invoice.pdf")
print("subtotal", subtotal, "vat", vat, "total", grand)
