#!/usr/bin/env node
// scripts/brand/verify.mjs — Contrôle de marque sur le répertoire publié public/ (brief marque §8).
//  - chaque page porte exactement le jeu de déclarations d'icônes du §6, aucune data: URI ;
//  - chaque URL référencée (icônes, manifeste, logo JSON-LD, og:image) existe, dimensions réelles
//    = déclarées, icônes carrées, .ico = 16/32/48, apple-touch et maskable sans canal alpha ;
//  - JSON-LD parsable (Organization logo ImageObject + alternateName, WebSite « Prim ») ;
//  - google-site-verification présent, aucun id dupliqué, aucun « PrimApp » ;
//  - _headers : ni noindex ni immutable sur les fichiers de marque.
// Sans dépendance (en-têtes PNG et ICO lus à la main). Code de sortie ≠ 0 si un contrôle échoue.

import { readFile, readdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const PUBLIC = join(ROOT, "public");
const SITE_URL = "https://primapp.dev";

// Jeu exact du §6, dans l'ordre.
const ICON_SET = [
  '<link rel="icon" href="/favicon.ico" sizes="16x16 32x32 48x48">',
  '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
  '<link rel="icon" href="/favicon-96x96.png" type="image/png" sizes="96x96">',
  '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
  '<link rel="manifest" href="/site.webmanifest">',
  '<meta name="apple-mobile-web-app-title" content="Prim">',
];
const OPAQUE = ["apple-touch-icon.png", "icon-maskable-512.png"];

const errors = [];
let passed = 0;
function check(cond, label) {
  if (cond) passed++;
  else errors.push(label);
  return cond;
}

// ---------- lecture d'images ----------
function pngInfo(buf) {
  if (buf.subarray(0, 8).toString("hex") !== "89504e470d0a1a0a") return null;
  const width = buf.readUInt32BE(16);
  const height = buf.readUInt32BE(20);
  const colorType = buf[25];
  let trns = false;
  for (let off = 8; off < buf.length; ) {
    const len = buf.readUInt32BE(off);
    const type = buf.subarray(off + 4, off + 8).toString("latin1");
    if (type === "tRNS") trns = true;
    if (type === "IEND") break;
    off += 12 + len;
  }
  // Canal alpha : types 4 (gris + alpha) et 6 (RVB + alpha), ou transparence tRNS.
  return { width, height, colorType, alpha: colorType === 4 || colorType === 6 || trns };
}

function icoSizes(buf) {
  if (buf.readUInt16LE(0) !== 0 || buf.readUInt16LE(2) !== 1) return null;
  const n = buf.readUInt16LE(4);
  const out = [];
  for (let i = 0; i < n; i++) {
    const e = 6 + 16 * i;
    const w = buf[e] || 256;
    const h = buf[e + 1] || 256;
    const size = buf.readUInt32LE(e + 8);
    const off = buf.readUInt32LE(e + 12);
    const png = pngInfo(buf.subarray(off, off + size));
    out.push({ w, h, real: png ? [png.width, png.height] : [w, h] });
  }
  return out;
}

async function htmlFiles(dir) {
  const out = [];
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) out.push(...(await htmlFiles(p)));
    else if (e.name.endsWith(".html")) out.push(p);
  }
  return out;
}

const local = (url) => join(PUBLIC, url.replace(SITE_URL, "").replace(/^\//, ""));

async function main() {
  // ---------- fichiers ----------
  const images = {};
  for (const name of ["favicon-96x96.png", "apple-touch-icon.png", "icon-192.png", "icon-512.png",
                      "icon-maskable-512.png", "prim-logo-512.png", "og-image.png"]) {
    const p = join(PUBLIC, name);
    if (!check(existsSync(p), `fichier absent : public/${name}`)) continue;
    images[name] = pngInfo(await readFile(p));
    check(images[name] !== null, `${name} : PNG illisible`);
  }
  const expectSize = { "favicon-96x96.png": 96, "apple-touch-icon.png": 180, "icon-192.png": 192, "icon-512.png": 512,
                       "icon-maskable-512.png": 512, "prim-logo-512.png": 512 };
  for (const [name, px] of Object.entries(expectSize)) {
    const im = images[name];
    if (im) check(im.width === px && im.height === px, `${name} : ${im.width}×${im.height} au lieu de ${px}×${px}`);
  }
  for (const name of OPAQUE) {
    if (images[name]) check(!images[name].alpha, `${name} : canal alpha présent (type ${images[name].colorType})`);
  }
  const og = images["og-image.png"];
  if (og) check(og.width === 1200 && og.height === 630, `og-image.png : ${og.width}×${og.height}`);
  const ico = existsSync(join(PUBLIC, "favicon.ico")) ? icoSizes(await readFile(join(PUBLIC, "favicon.ico"))) : null;
  if (check(ico !== null, "favicon.ico absent ou illisible")) {
    check(JSON.stringify(ico.map((e) => e.w).sort((a, b) => a - b)) === "[16,32,48]", `favicon.ico : tailles ${ico.map((e) => e.w)}`);
    check(ico.every((e) => e.w === e.h && e.real[0] === e.w && e.real[1] === e.h), "favicon.ico : entrées non carrées ou dimensions réelles ≠ déclarées");
  }
  const svg = existsSync(join(PUBLIC, "favicon.svg")) ? await readFile(join(PUBLIC, "favicon.svg"), "utf8") : "";
  check(/^<svg [^>]*viewBox="0 0 16 16"/.test(svg) && !/<image|href=|<script/.test(svg), "favicon.svg : absent, non carré ou contenu externe");

  // ---------- manifeste ----------
  const manifest = JSON.parse(await readFile(join(PUBLIC, "site.webmanifest"), "utf8"));
  check(manifest.name === "Prim" && manifest.short_name === "Prim", "manifeste : name/short_name ≠ « Prim »");
  check(manifest.theme_color === "#08090c" && manifest.background_color === "#08090c", "manifeste : couleurs ≠ #08090c");
  check(manifest.start_url === "/" && manifest.display === "browser", "manifeste : start_url ou display");
  const purposes = manifest.icons.map((i) => `${i.sizes}:${i.purpose}`).sort().join(",");
  check(purposes === "192x192:any,512x512:any,512x512:maskable", `manifeste : icônes ${purposes}`);
  check(!manifest.icons.some((i) => /any maskable|maskable any/.test(i.purpose)), "manifeste : purpose « any maskable » interdit");
  for (const i of manifest.icons) {
    const im = images[i.src.replace(/^\//, "")];
    const [w, h] = i.sizes.split("x").map(Number);
    check(im && im.width === w && im.height === h, `manifeste : ${i.src} ≠ ${i.sizes}`);
  }

  // ---------- pages ----------
  const pages = await htmlFiles(PUBLIC);
  for (const file of pages) {
    const rel = relative(PUBLIC, file);
    const html = await readFile(file, "utf8");
    const head = html.slice(0, html.indexOf("</head>"));
    for (const line of ICON_SET) {
      check(head.split(line).length - 1 === 1, `${rel} : déclaration absente ou dupliquée : ${line}`);
    }
    const iconLinks = head.match(/<link[^>]+rel="(?:icon|shortcut icon|apple-touch-icon|manifest|mask-icon)"[^>]*>/g) || [];
    check(iconLinks.length === 5, `${rel} : ${iconLinks.length} liens d'icône/manifeste au lieu de 5`);
    check(!iconLinks.some((l) => l.includes("data:")), `${rel} : data: URI dans un lien d'icône`);
    const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]);
    const dup = ids.filter((id, i) => ids.indexOf(id) !== i);
    check(dup.length === 0, `${rel} : id dupliqués ${[...new Set(dup)]}`);
    check(!/PrimApp/.test(html), `${rel} : « PrimApp » présent`);
    if (/^(en\/)?404\.html$/.test(rel)) continue;         // pages 404 statiques noindex (FR et /en/), hors gabarit
    check(/<meta name="google-site-verification" content="[^"]+">/.test(head), `${rel} : google-site-verification absent`);
    const ogImg = head.match(/<meta property="og:image" content="([^"]+)">/);
    const ogW = head.match(/<meta property="og:image:width" content="(\d+)">/);
    const ogH = head.match(/<meta property="og:image:height" content="(\d+)">/);
    const ogAlt = head.match(/<meta property="og:image:alt" content="([^"]+)">/);
    check(ogImg && existsSync(local(ogImg[1])) && og && +ogW[1] === og.width && +ogH[1] === og.height,
          `${rel} : og:image absente ou dimensions déclarées ≠ réelles`);
    check(ogAlt && /PRIM/.test(ogAlt[1]), `${rel} : og:image:alt ne décrit pas l'image (${ogAlt && ogAlt[1]})`);
    const blocks = [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)];
    check(blocks.length === 1, `${rel} : ${blocks.length} blocs JSON-LD`);
    for (const b of blocks) {
      let graph;
      try { graph = JSON.parse(b[1])["@graph"]; } catch { check(false, `${rel} : JSON-LD non parsable`); continue; }
      const org = graph.find((n) => n["@id"] === `${SITE_URL}/#prim`);
      if (check(org, `${rel} : Organization #prim absente`)) {
        const logo = org.logo || {};
        const im = images[(logo.url || "").replace(`${SITE_URL}/`, "")];
        check(logo["@type"] === "ImageObject" && im && im.width === logo.width && im.height === logo.height && logo.width >= 112,
              `${rel} : logo JSON-LD ≠ ImageObject aux dimensions réelles (≥ 112 px)`);
        check(JSON.stringify(org.alternateName) === '["Prim Studio"]' && org.name === "Prim", `${rel} : Organization name/alternateName`);
      }
      const web = graph.find((n) => n["@type"] === "WebSite");
      if (web) check(web.name === "Prim" && JSON.stringify(web.alternateName) === '["Prim Studio"]', `${rel} : WebSite name/alternateName`);
    }
  }

  // ---------- en-têtes HTTP ----------
  const headers = (await readFile(join(PUBLIC, "_headers"), "utf8"))
    .split("\n").filter((l) => !l.trim().startsWith("#")).join("\n");      // commentaires exclus
  check(!/noindex/i.test(headers), "_headers : X-Robots-Tag noindex présent");
  check(!/immutable/i.test(headers), "_headers : immutable sur une URL non versionnée");

  if (errors.length) {
    console.error(`✗ ${errors.length} contrôle(s) en échec :`);
    for (const e of errors) console.error(`  - ${e}`);
    process.exit(1);
  }
  console.log(`✓ Marque : ${passed} contrôles OK sur ${pages.length} pages (public/).`);
}

main().catch((e) => {
  console.error("✗ verify brand :", e);
  process.exit(1);
});
