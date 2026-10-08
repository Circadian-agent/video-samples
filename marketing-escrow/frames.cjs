const { chromium } = require("playwright");
const FPS = +process.env.FPS || 24, DUR = 36, only = process.env.ONLY ? process.env.ONLY.split(",").map(Number) : null;
(async () => {
const u = new URL(process.env.HTTPS_PROXY);
const b = await chromium.launch({ args: ["--no-sandbox"], proxy: { server: `${u.protocol}//${u.host}`, username: decodeURIComponent(u.username), password: decodeURIComponent(u.password) } });
const p = await b.newPage({ viewport: { width: 540, height: 960 }, deviceScaleFactor: 2 });
await p.goto("file://" + __dirname + "/" + (process.env.PAGE || "video.html"), { waitUntil: "networkidle" });
await p.evaluate(() => document.fonts.ready);
const ts = only || Array.from({ length: FPS * DUR }, (_, i) => i / FPS);
const W = +process.env.W || 1, K = +process.env.K || 0;
for (let i = K; i < ts.length; i += W) {
  await p.evaluate(t => render(t), ts[i]);
  await p.screenshot(only ? { path: `test_${ts[i]}.png` } : { path: `f/${String(i).padStart(5, "0")}.jpg`, type: "jpeg", quality: 92 });
}
await b.close();
})();
