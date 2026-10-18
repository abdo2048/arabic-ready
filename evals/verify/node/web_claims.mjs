import { chromium } from "playwright";
const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
const p = await b.newPage({ viewport: { width: 500, height: 300 } });
await p.setContent(`<html dir="rtl" lang="ar"><body style="margin:0">
<div id=s style="width:200px;overflow-x:auto;white-space:nowrap"><span style="display:inline-block;width:600px">x</span></div>
<div style="width:300px"><span id=f style="float:inline-start;width:50px;height:10px;background:red"></span></div>
<input id=r type=range value=20 style="width:300px"><progress id=g value=20 max=100 style="width:300px"></progress>
<div id=fx style="display:flex;width:300px"><span id=a style="width:50px">a</span><span>b</span></div>
<div id=jl style="display:flex;justify-content:left;width:300px"><span id=j style="width:50px">c</span></div>
</body></html>`);
const r = await p.evaluate(() => {
  const s = document.getElementById("s"); const start = s.scrollLeft; s.scrollLeft = -9999; const end = s.scrollLeft;
  const x = id => Math.round(document.getElementById(id).getBoundingClientRect().x);
  return { scrollLeft_start: start, scrollLeft_end: end, float_inline_start_x: x("f"), flex_first_child_x: x("a"), justify_left_x: x("j") };
});
console.log(r, await p.evaluate(() => navigator.userAgent.match(/Chrome\/[\d.]+/)[0]));
await p.screenshot({ path: "../out/web_range.png", clip: { x: 0, y: 20, width: 500, height: 60 } });
await b.close();
