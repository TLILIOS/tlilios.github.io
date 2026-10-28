# primapp.dev — site du studio Prim

Site vitrine **studio-first** du studio Prim (applications iOS natives premium) et de son fondateur TLILI HAMDI. Build statique Node minimal, bilingue FR/EN servi à l'URL, déployé sur Cloudflare Workers Static Assets.

> Auteur : **TLILI HAMDI**. Refonte studio-first : objectif primaire = studio + apps (racine `/`) ; objectif secondaire = CDI / mission (`/a-propos`). Séparation **par URL**, jamais dans un même hero.

## Architecture

- **Sources de vérité** dans `content/` — aucun HTML dupliqué :
  - `site.json` — chrome global bilingue (nav, footer, switcher, CTA, méta, sociaux).
  - `apps.json` — registre des apps (status-aware, `_draft` à valider). **Ajouter une app = éditer ce fichier.**
  - `routes.js` — table canonique des routes (**unique source** du hreflang réciproque et du sitemap).
  - `config.json` — `SITE_URL`, `LOCALES`, `X_DEFAULT`, `ENABLE_EMAIL_CAPTURE` (fail-safe `false`).
  - `pages/*.json` — corps éditorial bilingue de chaque page (home, fichechef, about, légales).
- **Pipeline** dans `scripts/` :
  - `build.mjs` — lit `content/`, valide les schémas (échec si invalide), rend chaque page FR (racine) + EN (`/en/`), génère `<head>`/hreflang/canonical/JSON-LD, `sitemap.xml`, `robots.txt`, écrit `assets/site.css`, copie `_headers`/AASA. Idempotent, déterministe.
  - `lib/` — `templates.mjs`, `render-pages.mjs`, `jsonld.mjs` (status-aware), `validate.mjs`, `styles.mjs`.
  - `verify.mjs` — réciprocité hreflang + canonical + sitemap/robots + AASA content-type.
  - `a11y-gate.mjs` — gate axe-core (Chrome headless), échec sur toute violation WCAG2AA.
  - `serve-dist.mjs` — serveur local pour valider `dist/`.

La sortie est écrite dans **`public/`** (dossier servi par l'app Git-connectée) **et** dans `dist/` (miroir vérifiable pour les validations). Cf. `docs/adr/0001-architecture-build-statique.md`.

## Build

```bash
npm install          # html-validate, pa11y-ci, axe-core, puppeteer, wrangler (4.98.0 pinné)
npm run build        # génère public/ + dist/
```

`public/` est **généré** — ne pas l'éditer à la main. Éditer `content/` puis `npm run build`.

## Validations

```bash
npm run verify        # réciprocité hreflang, canonical, sitemap/robots, AASA content-type
npm run validate:html # html-validate sur dist/ (0 erreur attendu)
npm run validate:a11y # gate axe-core sur 16 routes (0 violation WCAG2AA)
npm run validate      # build + les trois ci-dessus enchaînés
```

Le gate a11y nécessite Google Chrome (chemin macOS par défaut, sinon `PUPPETEER_EXECUTABLE_PATH`).

## Smoke test local

```bash
npm run dev           # wrangler dev (4.98.0 — la 4.99 a une régression dev)
# puis : curl -sL http://localhost:8787/fichechef  (clean URL → 307 → 200)
```

## Déploiement

**Aucun `wrangler deploy` manuel.** Le déploiement se fait par **`git push` sur `main`** : l'app Cloudflare Git-connectée `primapp-portfolio` (Workers Builds) reconstruit et publie automatiquement `./public`. Le custom domain `primapp.dev` est attaché à l'app dans le dashboard (DNS + certificat Cloudflare). `www.primapp.dev` est porté par le worker dédié `redirect-www/` (301 → apex). Un double canal de déploiement a déjà cassé la prod (audit 2026-06-10) — ne pas réintroduire.

## Ajouter une app

1. Ajouter un objet dans `content/apps.json` (schéma validé au build : `id` kebab unique, `status`, `tagline`/`summary` bilingues, `appStoreUrl`/`testflightUrl`/`appStoreId` = `null` tant que non publié).
2. La carte n'apparaît sur la home que si `showOnHome` ET (`status ∈ {available, coming-soon}` OU au moins une capture réelle). Les `concept` sans visuel restent en ligne « À l'étude ».
3. Une **page produit dédiée** ne naît qu'au **lancement** : créer `content/pages/<app>.json`, ajouter la route dans `content/routes.js` (FR + EN), rebuild. Avant lancement, l'app vit en section sur la home (anti-vaporware).
4. Au lancement : renseigner `appStoreUrl` (le CTA devient un vrai lien), `appStoreId` (Smart App Banner), déposer les captures sous `public/assets/<app>/`, et le fichier AASA si universal links.

## Marque (logo, favicons)

Outillage Python local (`scripts/brand/`, rien au runtime du site), venv gitignoré, rendu SVG par `rsvg-convert` :

```bash
python3 -m venv .venv-brand && .venv-brand/bin/python -m pip install -r scripts/brand/requirements.txt
brew install librsvg
.venv-brand/bin/python scripts/brand/generate.py   # régénère les fichiers de marque de public/ (idempotent)
npm run build                                      # puis miroir dist/ et pages
```

- **Sources validées** (planche V1, option A) : `docs/brand/source/*.svg` — volontairement hors de `assets/`, que le build copierait dans `public/`.
- **`generate.py`** écrit à la racine de `public/`, URL stables : `favicon.ico` (16/32/48), `favicon.svg` et `favicon-96x96.png` (variante simplifiée, lisible à 18 px dans Google), `apple-touch-icon.png` (180, opaque), `icon-192.png`, `icon-512.png`, `icon-maskable-512.png`, `prim-logo-512.png` (logo JSON-LD), `og-image.png` (1200 × 630).
- **Reconstruction** depuis la maquette (`.brand-reference/`, gitignorée, jamais publiée — elle porte des marques Apple) : `measure.py` → `construct.py` (≈ 7 min) → `sheet.py` (planche `docs/brand/previews/v1-sheet.png`).

## AASA / Universal Links

Le fichier `public/.well-known/apple-app-site-association` doit être servi en `Content-Type: application/json`. Le mécanisme retenu est **`public/_headers`** (supporté nativement par Cloudflare Workers Static Assets), qui force ce content-type sur cette route. La règle est **déjà en place et préservée par le build**. ⚠ Le **fichier AASA lui-même n'existe pas encore** (FicheChef non publié) — le déposer à la publication (cf. `TODO-CONTENT.md`). Cf. `docs/adr/0001`.

## Collecte d'email (désactivée)

`content/config.json` → `ENABLE_EMAIL_CAPTURE: false` (fail-safe). Aucun formulaire, page confidentialité inchangée. Passer à `true` impose **aussi** de mettre à jour la confidentialité (base légale, finalité, sous-traitant EU, durée) — ne jamais activer la collecte PII implicitement.

## Décisions d'architecture

`docs/adr/0001-architecture-build-statique.md`, `0002-i18n-hreflang.md`, `0003-accessibilite-gate.md`. Note de design : `docs/DESIGN-refonte.md`.
