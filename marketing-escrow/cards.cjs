const { chromium } = require("playwright");
(async () => {
const u = new URL(process.env.HTTPS_PROXY);
const b = await chromium.launch({ args: ["--no-sandbox"], proxy: { server: `${u.protocol}//${u.host}`, username: decodeURIComponent(u.username), password: decodeURIComponent(u.password) } });
const p = await b.newPage({ viewport: { width: 540, height: 675 }, deviceScaleFactor: 2 });
await p.goto("file://" + __dirname + "/cards.html", { waitUntil: "networkidle" });
await p.evaluate(() => document.fonts.ready);
for (let n = 1; n <= 4; n++) { await p.evaluate(n => show(n), n); await p.screenshot({ path: `post-${n}.png` }); }
await b.close();
})();
