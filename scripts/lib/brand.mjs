// scripts/lib/brand.mjs — Mot-symbole PRIM en SVG intégré (en-tête, pied de page).
// Lu au build depuis la source validée (docs/brand/source/prim-wordmark-light.svg, planche V1) :
// une seule source de vérité pour la géométrie. Couleur héritée (currentColor → --text-primary).

import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const SOURCE = readFileSync(join(ROOT, "docs/brand/source/prim-wordmark-light.svg"), "utf8");
const VIEWBOX = SOURCE.match(/viewBox="([^"]+)"/)[1];
const [, , VB_W, VB_H] = VIEWBOX.split(" ").map(Number);
const D = [...SOURCE.matchAll(/<path fill="[^"]+" d="([^"]+)"/g)].map((m) => m[1]).join("");
if (!D) throw new Error("brand.mjs : chemins du mot-symbole introuvables");

// Hauteur de capitale de Georgia (sCapHeight 1419/2048) : PRIM prend la place exacte des capitales
// de l'ancien logo texte « Prim » (même boîte de ligne, CLS nul). Reprise dans styles.mjs (.wordmark).
export const CAP_EM = 0.6929;

// `fontPx` : taille de police du conteneur, pour des width/height explicites avant chargement du CSS.
// `decorative` : true dans un lien déjà nommé (aria-hidden) ; sinon image nommée « Prim ».
export function wordmark({ fontPx, decorative }) {
  const h = fontPx * CAP_EM;
  const w = (h * VB_W) / VB_H;
  const a11y = decorative ? 'aria-hidden="true" focusable="false"' : 'role="img" aria-label="Prim"';
  return `<svg class="wordmark" viewBox="${VIEWBOX}" width="${w.toFixed(2)}" height="${h.toFixed(2)}" ${a11y}><path fill="currentColor" d="${D}"/></svg>`;
}
