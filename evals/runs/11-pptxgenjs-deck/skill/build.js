// Arabic (RTL) single-slide deck for a Saudi client.
const pptxgen = require("pptxgenjs");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_16x9";          // 10 x 5.625 in
pptx.rtlMode = true;                  // presentation-level RTL
pptx.lang = "ar-SA";
pptx.title = "خطة الإطلاق 2026";

// RTL options must go on every run AND on the outer addText options (pptxgenjs 4.x)
const ar = { rtlMode: true, align: "right", lang: "ar-SA", fontFace: "Arial", color: "1F2937" };

const slide = pptx.addSlide();
slide.background = { color: "FFFFFF" };

// Accent bar on the start (right) side
slide.addShape(pptx.ShapeType.rect, { x: 9.55, y: 0.6, w: 0.12, h: 0.9, fill: { color: "006C35" }, line: { color: "006C35" } });

// Title
slide.addText([{ text: "خطة الإطلاق 2026", options: { ...ar, fontSize: 36, bold: true, color: "006C35" } }],
  { x: 0.5, y: 0.5, w: 8.9, h: 1.1, valign: "middle", ...ar, fontSize: 36, bold: true });

// Bullets (bullets appear on the right because each paragraph is rtl="1")
const items = [
  "المرحلة الأولى: يناير – مارس",
  "ميزانية 1.2 مليون ريال",
  "فريق من 15 شخصًا (Product + Engineering)",
];
slide.addText(
  items.map((t, i) => ({ text: t, options: { ...ar, fontSize: 24, bullet: { indent: 24 }, breakLine: i < items.length - 1, paraSpaceAfter: 14 } })),
  { x: 0.5, y: 1.9, w: 8.9, h: 3.0, valign: "top", lineSpacingMultiple: 1.3, ...ar, fontSize: 24 }
);

pptx.writeFile({ fileName: "deck.pptx" }).then(f => console.log("wrote", f));
