// usage: node shot.mjs in.html out.png [width] [pdf]
import { chromium } from "playwright";
const [inp, out, width = "600", pdf] = process.argv.slice(2);
const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
const p = await b.newPage({ viewport: { width: +width, height: 400 }, deviceScaleFactor: 1.5 });
await p.goto("file://" + inp); await p.waitForTimeout(300);
await p.screenshot({ path: out, fullPage: true });
if (pdf) await p.pdf({ path: pdf, printBackground: true });
await b.close();
