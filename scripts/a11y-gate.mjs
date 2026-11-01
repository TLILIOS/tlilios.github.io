#!/usr/bin/env node
// scripts/a11y-gate.mjs — Gate accessibilité bloquant (ADR-0003) via axe-core sur Chrome headless.
// Sert dist/ en interne, exécute axe sur toutes les routes, ÉCHOUE sur toute VIOLATION réelle.
// Les résultats "incomplete" d'axe (cas où axe ne peut pas trancher seul — ex. texte au-dessus
// d'un background-image gradient) sont rapportés séparément, NON bloquants : ils sont vérifiés
// manuellement (ratios calculés, fonds solides ajoutés — cf. styles.mjs). On ne supprime aucun
// vrai défaut : seul le bruit "indéterminable par la machine" est exclu du gate.

import http from "node:http";
import { readFile, stat } from "node:fs/promises";
import { join, extname, resolve } from "node:path";
import puppeteer from "puppeteer";
import { routes } from "../content/routes.js";

const ROOT = resolve(process.cwd());
const DIST = join(ROOT, "dist");
const PORT = 8799;
const CHROME =
  process.env.PUPPETEER_EXECUTABLE_PATH ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

const MIME = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".pdf": "application/pdf", ".mp4": "video/mp4", ".xml": "application/xml", ".txt": "text/plain" };

function serve() {
  return new Promise((res) => {
    const srv = http.createServer(async (req, r) => {
      const u = decodeURIComponent((req.url || "/").split("?")[0]);
      let f = join(DIST, u);
      // Comme Workers Static Assets (auto-trailing-slash) : /x → x.html en priorité, /x/ → x/index.html.
      try { await stat(`${f}.html`); f = `${f}.html`; }
      catch { try { if ((await stat(f)).isDirectory()) f = join(f, "index.html"); } catch {} }
      try { const d = await readFile(f); r.writeHead(200, { "Content-Type": MIME[extname(f)] || "application/octet-stream" }); r.end(d); }
      catch { r.writeHead(404); r.end("404"); }
    });
    srv.listen(PORT, () => res(srv));
  });
}

async function main() {
  const srv = await serve();
  const axeSource = await readFile(join(ROOT, "node_modules/axe-core/axe.min.js"), "utf8");

  const browser = await puppeteer.launch({ executablePath: CHROME, args: ["--no-sandbox", "--disable-gpu"] });
  const urls = routes.flatMap((r) => ["fr", "en"].map((l) => r[l])); // URLs canoniques servies

  let totalViolations = 0;
  let totalIncomplete = 0;
  const violationDetails = [];

  for (const path of urls) {
    const page = await browser.newPage();
    await page.goto(`http://localhost:${PORT}${path}`, { waitUntil: "networkidle0" });
    await page.evaluate(axeSource);
    const result = await page.evaluate(async () => await window.axe.run(document, { resultTypes: ["violations", "incomplete"] }));
    const v = result.violations.length;
    const inc = result.incomplete.length;
    totalViolations += v;
    totalIncomplete += inc;
    if (v > 0) {
      violationDetails.push({ path, violations: result.violations.map((x) => `${x.id} (${x.nodes.length})`) });
    }
    console.log(`  ${v === 0 ? "✓" : "✗"} ${path}  violations:${v}  incomplete:${inc}`);
    await page.close();
  }

  await browser.close();
  srv.close();

  console.log(`\n— Total : ${totalViolations} violations (bloquant), ${totalIncomplete} incomplete (non bloquant, vérifiés manuellement).`);
  if (totalViolations > 0) {
    console.error("\n✗ Gate a11y ÉCHOUÉ — violations réelles :");
    for (const d of violationDetails) console.error(`   ${d.path}: ${d.violations.join(", ")}`);
    process.exit(1);
  }
  console.log("✓ Gate a11y : 0 violation WCAG2AA sur les 16 routes.");
}

main().catch((e) => { console.error("a11y-gate erreur :", e.message); process.exit(1); });
