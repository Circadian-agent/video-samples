const { chromium } = require("playwright");
(async () => { const b = await chromium.launch({ args: ["--no-sandbox"] });
const p = await b.newPage({ viewport: { width: 540, height: 960 }, deviceScaleFactor: 2 });
await p.setContent(`<body style="margin:0;background:transparent"><svg width="540" height="960"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="4"/><feColorMatrix values="0 0 0 0 .3  0 0 0 0 .25  0 0 0 0 .2  0 0 0 .55 0"/></filter><rect width="540" height="960" filter="url(#n)"/></svg></body>`);
await p.screenshot({ path: "grain.png", omitBackground: true }); await b.close(); })();
