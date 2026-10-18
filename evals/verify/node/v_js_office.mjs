import fs from "fs";
import { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, AlignmentType, HeadingLevel, WidthType } from "docx";
import pptxgen from "pptxgenjs";
const OUT = new URL("../out/", import.meta.url).pathname;
const TEXT = "فاتورة رقم 1024 للعميل Acme، الإجمالي 49.99 دولار؟";
const run = (text, o = {}) => new TextRun({ text, rightToLeft: true, font: { ascii: "Noto Naskh Arabic", hAnsi: "Noto Naskh Arabic", cs: "Noto Naskh Arabic" }, size: 28, sizeComplexScript: 28, ...o });
const P = (text, o = {}) => new Paragraph({ bidirectional: true, children: [run(text, o)] });
const cell = (t) => new TableCell({ children: [P(t, { size: 24, sizeComplexScript: 24 })], width: { size: 3000, type: WidthType.DXA } });
const doc = new Document({ sections: [{ children: [
  P("تقرير المبيعات", { bold: true, boldComplexScript: true, size: 40, sizeComplexScript: 40 }),
  P(TEXT, { bold: true, boldComplexScript: true }),
  new Table({ visuallyRightToLeft: true, rows: [
    new TableRow({ children: ["المنتج", "الكمية", "السعر"].map(cell) }),
    new TableRow({ children: ["قلم", "3", "12.50"].map(cell) }) ] }),
]}]});
fs.writeFileSync(OUT + "docxjs_fixed.docx", await Packer.toBuffer(doc));

for (const mode of ["naive", "fixed"]) {
  const p = new pptxgen(); p.defineLayout({ name: "W", width: 10, height: 3 }); p.layout = "W";
  const s = p.addSlide();
  const o = mode === "fixed" ? { rtlMode: true, align: "right", lang: "ar-SA", fontFace: "Noto Naskh Arabic" } : {};
  s.addText([
    { text: "نتائج الربع الثالث", options: { fontSize: 28, breakLine: true } },
    { text: TEXT, options: { fontSize: 20, breakLine: true } },
    { text: "نمو 25% مقارنة بالعام الماضي", options: { fontSize: 20, bullet: true } },
  ], { x: 0.5, y: 0.3, w: 9, h: 2.4, valign: "top", ...o });
  await p.writeFile({ fileName: OUT + `pptxgenjs_${mode}.pptx` });
}
console.log("docx", JSON.parse(fs.readFileSync(new URL("./node_modules/docx/package.json", import.meta.url))).version,
  "pptxgenjs", JSON.parse(fs.readFileSync(new URL("./node_modules/pptxgenjs/package.json", import.meta.url))).version);
