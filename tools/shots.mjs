// OG images + favicon PNGs + screenshots. Usage: node shots.mjs og|shots <baseUrl>
import { chromium } from "playwright";
import fs from "fs";
import path from "path";
const mode = process.argv[2];
const here = path.dirname(new URL(import.meta.url).pathname);
const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" }).catch(async () => chromium.launch());
if (mode === "og") {
  const data = JSON.parse(fs.readFileSync(path.join(here, "../data/fintech-capstone.json")));
  const by = data.by_year; const mx = Math.max(...by.map(r => r.total_amount));
  const bars = by.map(r => `<i style="height:${(r.total_amount / mx * 100).toFixed(1)}%"></i>`).join("");
  const x = by.map(r => `<span>${String(r.issue_year).slice(2)}</span>`).join("");
  const url = process.argv[3] || "danielgalea.vercel.app";
  const variants = {
    "og-es": { EYEBROW: "Data Analyst junior · Granada", LEAD: "Ingeniería Informática y Matemáticas (UGR) · <b>SQL, BigQuery, Looker y LookML</b> con datos reales.", CARDT: "importe prestado por año", K1: "852,4 M$ en 2019", K2: "×24 desde 2012", TAG: "Portfolio · ES" },
    "og-en": { EYEBROW: "Junior Data Analyst · Granada", LEAD: "Computer Engineering & Maths student · <b>SQL, BigQuery, Looker and LookML</b> on real data.", CARDT: "amount lent per year", K1: "$852.4M in 2019", K2: "24× since 2012", TAG: "Portfolio · EN" },
    "og-case-es": { EYEBROW: "Caso · TheLook Fintech", LEAD: "Salud de una cartera de <b>270.299 préstamos</b>: de BigQuery a un dashboard en Looker para Tesorería.", CARDT: "fintech.loan · importe por año", K1: "3.080,6 M$ pendientes", K2: "límite 3.000 M$", TAG: "Caso práctico" },
    "og-case-en": { EYEBROW: "Case study · TheLook Fintech", LEAD: "Health of a <b>270,299-loan</b> portfolio: from BigQuery to a Looker dashboard for Treasury.", CARDT: "fintech.loan · amount per year", K1: "$3.08B outstanding", K2: "limit $3.0B", TAG: "Case study" },
  };
  const tpl = fs.readFileSync(path.join(here, "og.html"), "utf8");
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
  for (const [name, v] of Object.entries(variants)) {
    let h = tpl.replace("__BARS__", bars).replace("__X__", x).replace("__URL__", url);
    for (const [k, val] of Object.entries(v)) h = h.replace(`__${k}__`, val);
    const f = path.join(here, `og-${name}.tmp.html`);
    fs.writeFileSync(f, h);
    await page.goto("file://" + f); await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(here, "../site/assets/img", `${name}.png`) });
    fs.unlinkSync(f);
  }
  // apple touch icon + favicon png
  const svg = fs.readFileSync(path.join(here, "../site/favicon.svg"), "utf8").replace(/<style>.*<\/style>/, "").replace('class="b"', 'fill="#141413"').replace(/class="f"/g, 'fill="#f7f6f2"');
  for (const [name, size, pad] of [["apple-touch-icon.png", 180, 0], ["favicon-32.png", 32, 0]]) {
    await page.setViewportSize({ width: size, height: size });
    await page.setContent(`<html><body style="margin:0;background:transparent">${svg.replace("<svg ", `<svg width="${size}" height="${size}" `)}</body></html>`);
    await page.screenshot({ path: path.join(here, "../site", name), omitBackground: true });
  }
} else if (mode === "shots") {
  const base = process.argv[3];
  const outDir = process.argv[4] || path.join(here, "shots");
  fs.mkdirSync(outDir, { recursive: true });
  const pages = ["/", "/en/", "/caso/thelook-fintech/", "/en/case-study/thelook-fintech/"];
  const report = [];
  for (const [vw, vh, tag] of [[1440, 900, "desktop"], [390, 844, "mobile"]]) {
    for (const scheme of ["light", "dark"]) {
      const ctx = await browser.newContext({ viewport: { width: vw, height: vh }, colorScheme: scheme, reducedMotion: "reduce", deviceScaleFactor: tag === "mobile" ? 2 : 1 });
      for (const p of pages) {
        if (scheme === "dark" && p.includes("en")) continue;
        const page = await ctx.newPage();
        const errors = [];
        page.on("console", m => { if (m.type() === "error" || m.type() === "warning") errors.push(m.type() + ": " + m.text()); });
        page.on("pageerror", e => errors.push("pageerror: " + e.message));
        const resp = await page.goto(base + p, { waitUntil: "networkidle" });
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
        const name = `${tag}-${scheme}${p.replace(/\//g, "_")}.png`;
        await page.screenshot({ path: path.join(outDir, name), fullPage: true });
        report.push({ page: p, tag, scheme, status: resp.status(), overflow, errors });
        await page.close();
      }
      await ctx.close();
    }
  }
  console.log(JSON.stringify(report, null, 1));
}
await browser.close();
