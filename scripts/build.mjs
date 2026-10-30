#!/usr/bin/env node
// scripts/build.mjs — Pipeline de build statique du site Prim (primapp.dev).
// Idempotent, déterministe (ordre stable, pas de timestamp volatil).
// Lit content/ → valide → rend FR + EN → head/hreflang/canonical/JSON-LD → sitemap/robots
// → écrit site.css → copie assets + _headers + AASA. Non-destructif sur les binaires.

import { readFile, writeFile, mkdir, readdir, copyFile, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { routes, outputPathFor } from "../content/routes.js";
import { validateAll } from "./lib/validate.mjs";
import { layout, videoModal } from "./lib/templates.mjs";
import { SITE_CSS } from "./lib/styles.mjs";
import { renderHome, renderApp, renderAbout, renderLegal } from "./lib/render-pages.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");
const CONTENT = join(ROOT, "content");
const PAGES = join(CONTENT, "pages");
// Cible de sortie : public/ (déjà servi par l'app Git-connectée — ADR-0001). dist/ = miroir vérifiable.
const OUT_PUBLIC = join(ROOT, "public");
const OUT_DIST = join(ROOT, "dist");
const SRC_ASSETS = join(ROOT, "assets"); // assets source (si présents) ; sinon binaires in-place préservés.

const readJson = async (p) => JSON.parse(await readFile(p, "utf8"));

// jumelle de route pour un type → template.
function bodyFor({ template, page, site, apps, app, lang, projectsDoc }) {
  switch (template) {
    case "home":
      return renderHome({ page, site, apps, lang });
    case "app":
      return renderApp({ page, site, app, lang });
    case "about":
      return renderAbout({ page, site, lang, projectsDoc });
    case "legal":
      return renderLegal({ page, site, lang });
    default:
      throw new Error(`Template inconnu : ${template}`);
  }
}

const JSONLD_TYPE = { home: "home", app: "app", about: "about", legal: "legal" };

async function writeOut(relPath, content, targets) {
  for (const base of targets) {
    const full = join(base, relPath);
    await mkdir(dirname(full), { recursive: true });
    await writeFile(full, content, "utf8");
  }
}

// Copie récursive non-destructive d'un dossier (assets binaires).
async function copyDir(src, targets) {
  if (!existsSync(src)) return 0;
  let count = 0;
  const entries = await readdir(src, { withFileTypes: true });
  for (const e of entries) {
    const s = join(src, e.name);
    if (e.isDirectory()) {
      count += await copyDir(s, targets.map((t) => join(t, e.name)));
    } else {
      for (const t of targets) {
        await mkdir(t, { recursive: true });
        await copyFile(s, join(t, e.name));
      }
      count++;
    }
  }
  return count;
}

function buildSitemap(SITE_URL, routes) {
  const urls = [];
  for (const r of routes) {
    for (const lang of ["fr", "en"]) {
      const loc = `${SITE_URL}${r[lang]}`;
      const frLoc = `${SITE_URL}${r.fr}`;
      const enLoc = `${SITE_URL}${r.en}`;
      urls.push(
        `  <url>\n` +
          `    <loc>${loc}</loc>\n` +
          `    <xhtml:link rel="alternate" hreflang="fr" href="${frLoc}"/>\n` +
          `    <xhtml:link rel="alternate" hreflang="en" href="${enLoc}"/>\n` +
          `    <xhtml:link rel="alternate" hreflang="x-default" href="${frLoc}"/>\n` +
          `    <changefreq>${r.sitemap.changefreq}</changefreq>\n` +
          `    <priority>${r.sitemap.priority}</priority>\n` +
          `  </url>`
      );
    }
  }
  return (
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n` +
    urls.join("\n") +
    `\n</urlset>\n`
  );
}

function buildRobots(SITE_URL) {
  return `# Robots.txt — Prim / primapp.dev\nUser-agent: *\nAllow: /\n\nSitemap: ${SITE_URL}/sitemap.xml\n`;
}

async function main() {
  const config = await readJson(join(CONTENT, "config.json"));
  const site = await readJson(join(CONTENT, "site.json"));
  const appsDoc = await readJson(join(CONTENT, "apps.json"));
  const apps = appsDoc.apps;
  // Démos portfolio fondateur (rendues sur /a-propos). Optionnel : absent → pas de section.
  const projectsDoc = existsSync(join(CONTENT, "projects.json"))
    ? await readJson(join(CONTENT, "projects.json"))
    : null;

  // 1. Validation (échec build si invalide).
  validateAll({ config, routes, appsDoc });

  const targets = [OUT_PUBLIC, OUT_DIST];
  const { SITE_URL } = config;

  // 2. site.css déterministe.
  await writeOut(join("assets", "site.css"), SITE_CSS, targets);

  // 3. Rendu de chaque route × FR/EN.
  let pageCount = 0;
  for (const route of routes) {
    const page = await readJson(join(PAGES, `${route.data}.json`));
    const app = route.appId ? apps.find((a) => a.id === route.appId) : undefined;
    for (const lang of config.LOCALES) {
      const pageL = page[lang];
      const pageMeta = {
        title: pageL.title,
        // Les pages légales portent déjà « | Prim » dans leur title (migration fidèle).
        titleHasSuffix: route.template === "legal",
        description: pageL.description,
        ogType: pageL.ogType || "website",
      };
      const bodyHtml = bodyFor({ template: route.template, page, site, apps, app, lang, projectsDoc });
      // La modale vidéo AA n'est injectée que sur /a-propos (seule page portant des démos).
      const extraHtml =
        route.template === "about" && projectsDoc
          ? videoModal({ i18n: projectsDoc.i18n[lang] })
          : "";
      const html = layout({
        site,
        config,
        lang,
        route,
        pageMeta,
        jsonldType: JSONLD_TYPE[route.template],
        app,
        bodyHtml,
        extraHtml,
      });
      // Nettoyage déterministe : trailing whitespace + lignes vides multiples (html-validate strict).
      const cleaned = html
        .split("\n")
        .map((l) => l.replace(/\s+$/, ""))
        .join("\n")
        .replace(/\n{3,}/g, "\n\n");
      const rel = outputPathFor(route[lang]);
      await writeOut(rel, cleaned, targets);
      pageCount++;
    }
  }

  // 4. sitemap + robots.
  await writeOut("sitemap.xml", buildSitemap(SITE_URL, routes), targets);
  await writeOut("robots.txt", buildRobots(SITE_URL), targets);

  // 5. _headers (AASA content-type) + .well-known (si présent) : copiés tels quels.
  const headersSrc = join(OUT_PUBLIC, "_headers");
  if (existsSync(headersSrc)) {
    const headers = await readFile(headersSrc, "utf8");
    await writeOut("_headers", headers, [OUT_DIST]); // public/_headers déjà en place, on mirroir vers dist.
  }
  const aasaSrc = join(OUT_PUBLIC, ".well-known", "apple-app-site-association");
  if (existsSync(aasaSrc)) {
    const aasa = await readFile(aasaSrc, "utf8");
    await writeOut(join(".well-known", "apple-app-site-association"), aasa, [OUT_DIST]);
  } else {
    console.warn(
      "  ⚠ AASA fichier absent (public/.well-known/apple-app-site-association). " +
        "Règle _headers préservée ; déposer le fichier à la publication FicheChef (TODO-CONTENT)."
    );
  }

  // 6. Assets binaires : si assets/ source existe, copie ; sinon binaires déjà in-place dans public/ préservés.
  let assetCount = 0;
  if (existsSync(SRC_ASSETS)) {
    assetCount = await copyDir(SRC_ASSETS, [join(OUT_PUBLIC, "assets"), join(OUT_DIST, "assets")]);
  }
  // Copie les pages 404 vers dist (public/404.html et public/en/404.html déjà en place) :
  // not_found_handling "404-page" sert le 404.html le plus proche, donc en/404.html sous /en/.
  for (const rel of ["404.html", join("en", "404.html")]) {
    const e404 = join(OUT_PUBLIC, rel);
    if (existsSync(e404)) await writeOut(rel, await readFile(e404, "utf8"), [OUT_DIST]);
  }
  // Binaires racine (mp4, posters, og-image, cv pdf, icônes, manifeste) : mirroir public→dist pour validations.
  const rootBin = await readdir(OUT_PUBLIC, { withFileTypes: true });
  for (const e of rootBin) {
    if (e.isFile() && /\.(mp4|jpg|jpeg|png|pdf|svg|webp|ico|vtt|webmanifest)$/i.test(e.name)) {
      await mkdir(OUT_DIST, { recursive: true });
      await copyFile(join(OUT_PUBLIC, e.name), join(OUT_DIST, e.name));
      assetCount++;
    }
  }

  console.log(`✓ Build OK — ${pageCount} pages (FR+EN), ${routes.length} routes, ${assetCount} assets copiés.`);
  console.log(`  Sortie : public/ (déployé) + dist/ (miroir vérifiable).`);
}

main().catch((err) => {
  if (err.isValidation) {
    console.error(`\n✗ ${err.message}\n`);
  } else {
    console.error("\n✗ Build échoué :", err);
  }
  process.exit(1);
});
