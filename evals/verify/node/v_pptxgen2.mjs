import pptxgen from "pptxgenjs";
const OUT = new URL("../out/", import.meta.url).pathname;
const TEXT = "فاتورة رقم 1024 للعميل Acme، الإجمالي 49.99 دولار؟";
const p = new pptxgen(); p.defineLayout({ name: "W", width: 10, height: 3 }); p.layout = "W";
const s = p.addSlide();
const ar = { rtlMode: true, align: "right", lang: "ar-SA", fontFace: "Noto Naskh Arabic" };
s.addText([
  { text: "نتائج الربع الثالث", options: { ...ar, fontSize: 28, breakLine: true } },
  { text: TEXT, options: { ...ar, fontSize: 20, breakLine: true } },
  { text: "نمو 25% مقارنة بالعام الماضي", options: { ...ar, fontSize: 20, bullet: true } },
], { x: 0.5, y: 0.3, w: 9, h: 1.8, valign: "top", ...ar });
s.addText(TEXT, { x: 0.5, y: 2.1, w: 9, h: 0.6, fontSize: 20, ...ar });
await p.writeFile({ fileName: OUT + "pptxgenjs_fixed.pptx" });
