const { chromium } = require("playwright");
const durs = [2.81,5.22,3.87,4.93,3.57], GAP = 0.6, LEAD = 1.0;
(async () => {
const u = new URL(process.env.HTTPS_PROXY);
const b = await chromium.launch({ args: ["--no-sandbox"], proxy: { server: `${u.protocol}//${u.host}`, username: decodeURIComponent(u.username), password: decodeURIComponent(u.password) } });
const ctx = await b.newContext({ viewport: { width: 1920, height: 1080 }, recordVideo: { dir: ".", size: { width: 1920, height: 1080 } } });
const t0 = Date.now();
const p = await ctx.newPage();
await p.goto("https://ai-freelance-hub.com/learn", { waitUntil: "networkidle" });
await p.addStyleTag({ content: `.hl{outline:4px solid #e0a040!important;outline-offset:6px;border-radius:6px;background:rgba(224,160,64,.12)!important;transition:all .3s}` });
await p.waitForTimeout(500);
const hl = async (text, scroll) => p.evaluate(([text, scroll]) => {
  document.querySelectorAll(".hl").forEach(e => e.classList.remove("hl"));
  const els = [...document.querySelectorAll("body *")].filter(e => e.textContent.trim().startsWith(text) && e.textContent.trim().length < text.length + 60); const el = els.sort((a,b)=>a.textContent.length-b.textContent.length).pop();
  if (!el) return false;
  const target = scroll === "card" ? el.closest("article,li,section>div,div") : el;
  if (scroll) el.scrollIntoView({ behavior: "smooth", block: "center" });
  (scroll === "card" ? el.parentElement : el).classList.add("hl");
  return true;
}, [text, scroll]);
const start = (Date.now() - t0) / 1000;
const steps = [["How escrow protects you", "card"], ["Funds sit with a third party", "x"], ["Released only when you accept", "x"], ["If there's a dispute", "x"], ["Where the money is", "x"]];
await p.waitForTimeout(LEAD * 1000 - 400);
for (let i = 0; i < steps.length; i++) {
  console.error(i, await hl(...steps[i]));
  await p.waitForTimeout((durs[i] + GAP) * 1000);
}
await p.waitForTimeout(1200);
await ctx.close(); await b.close();
console.log(JSON.stringify({ start, file: await p.video().path() }));
})();
