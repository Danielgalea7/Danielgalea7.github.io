// Element screenshots for the capstone README and LinkedIn posts.
import { chromium } from "playwright";
const base = "http://localhost:8765";
const out = process.argv[2];
const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
const ctx = await b.newContext({ viewport: { width: 1240, height: 900 }, deviceScaleFactor: 2, colorScheme: "light", reducedMotion: "reduce" });
const p = await ctx.newPage();
const shots = [
  ["/en/case-study/thelook-fintech/", ".dash", `${out}/thelook-fintech-capstone/docs/loan-insights-recreation.png`],
  ["/en/case-study/thelook-fintech/", ".arch .h", `${out}/thelook-fintech-capstone/docs/architecture.png`],
  ["/caso/thelook-fintech/", ".dash", `${out}/../linkedin-imagenes/01-capstone-dashboard.png`],
  ["/", "#p-rfm", `${out}/../linkedin-imagenes/02-rfm-ntile.png`],
  ["/", "#p-part", `${out}/../linkedin-imagenes/03-particionado.png`],
  ["/", "#data-journey .journey", `${out}/../linkedin-imagenes/04-data-journey.png`],
  ["/", "#p-dash", `${out}/../linkedin-imagenes/05-dashboard-ventas.png`],
];
for (const [url, sel, file] of shots) {
  await p.goto(base + url, { waitUntil: "networkidle" });
  await p.addStyleTag({ content: ".rv,.reveal .bars .bb,.reveal .cols .cb{opacity:1!important;transform:none!important} details.sql{display:none} .site-header{display:none!important} .projects{align-items:start}" });
  const el = await p.$(sel);
  await el.screenshot({ path: file });
  console.log("ok", file.split("/").slice(-2).join("/"));
}
await b.close();
