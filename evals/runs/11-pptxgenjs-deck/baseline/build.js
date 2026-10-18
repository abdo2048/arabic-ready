const pptxgen = require("pptxgenjs");
const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.rtlMode = true;
pptx.lang = "ar-SA";
pptx.title = "خطة الإطلاق 2026";

const FONT = "Noto Naskh Arabic";
const s = pptx.addSlide();
s.background = { color: "FFFFFF" };
s.addShape(pptx.ShapeType.rect, { x: 13.03, y: 0, w: 0.3, h: 7.5, fill: { color: "006C35" } });

s.addText("خطة الإطلاق 2026", {
  x: 0.6, y: 0.6, w: 12.0, h: 1.2,
  fontFace: FONT, fontSize: 40, bold: true, color: "006C35",
  align: "right", rtlMode: true, lang: "ar-SA",
});

const items = [
  "المرحلة الأولى: يناير – مارس",
  "ميزانية 1.2 مليون ريال",
  "فريق من 15 شخصًا (Product + Engineering)",
];
s.addText(
  items.map((t) => ({ text: t, options: { bullet: true, breakLine: true, rtlMode: true, align: "right", lang: "ar-SA" } })),
  {
    x: 0.6, y: 2.1, w: 12.0, h: 3.5,
    fontFace: FONT, fontSize: 26, color: "333333",
    align: "right", rtlMode: true, lang: "ar-SA",
    paraSpaceAfter: 14, valign: "top",
  }
);

pptx.writeFile({ fileName: "deck.pptx" }).then((f) => console.log("wrote", f));
