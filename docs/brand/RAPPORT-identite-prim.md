# Rapport — Suivi post-déploiement de l'identité Prim (primapp.dev)

| | |
|---|---|
| Auteur | TLILI HAMDI |
| Validé par | TLILI HAMDI |
| Date | 2026-10-28 (contrôle final à 21:01Z) |
| Dépôt | TLILIOS/tlilios.github.io — `main` = `2fe1d46` |
| Déploiement | push `main` → Workers Builds (app `primapp-portfolio`, sert `./public`) |
| Annexes | `seo-checklist-results.md` (un contrôle par ligne), `manual-actions.md` (actions manuelles) |

## Synthèse

| § | Point | Statut | Preuve |
|---|---|---|---|
| 3.1 | État réel (git + prod) | Vérifié, conforme à l'état du 28/10 | §1 |
| 3.2 | Search Console : test en direct puis demande d'indexation de `/` et `/en/` | Prérequis vérifiés publiquement : les deux pages sont indexables. Test en direct, demande d'indexation et contrôles du compte : action manuelle requise | §2 |
| 3.3 | Données structurées | Vérifié : JSON-LD valide sur 16 pages, logo conforme aux exigences Google. Rich Results Test : action manuelle requise (outil Google interactif, sans API publique) | §3 |
| 3.4 | Aperçus Facebook et LinkedIn | Balises et image vérifiées sur 16 pages, aucune anomalie. Nouveau scrape forcé : action manuelle requise | §4 |
| 3.5 | `Person.image` (P3) | Vérifié en prod (`2fe1d46`) | §5 |
| 3.6 | Always Use HTTPS | Partiellement conforme : HTTPS, certificat, HSTS et www → domaine sans www OK, mais `http://` répond sans 301. Correctif : réglage du dashboard Cloudflare, action manuelle requise | §6 |
| 3.6 | Wrangler | Non fait : `npx wrangler login` proposé (jeton expiré) | §6 |
| 3.6 | Branches fusionnées | Fait : supprimées en local | §6 |

## 1. État réel

### Git

```
$ git ls-remote origin main
2a16239a529bf939a0f08e3fccbe06fe6a05b804  refs/heads/main    # avant P3
2fe1d4631b47de84810ddd7cdd5a1517f25705e9  refs/heads/main    # après P3
```

Avant P3 : arbre propre, `main` = `origin/main` = `2a16239`, 6 commits `584af90..2a16239` au-dessus de `6437e60`.
`.brand-reference/` : gitignorée (`.gitignore:17`), aucun fichier suivi.

### Fichiers de marque

`curl -sS -D - -o <fichier> https://primapp.dev/<fichier>`, puis `shasum -a 256` comparé à `public/`.
Contrôles du 2026-10-28 à 03:16:12Z, 03:29:58Z (après P3) et 21:01:55Z, résultats identiques.

| Fichier | Statut | Content-Type | Cache-Control | SHA-256 (12 car.) |
|---|---|---|---|---|
| favicon.ico | 200 | image/vnd.microsoft.icon | public, max-age=0, must-revalidate | 01c07a967f8d = public/ |
| favicon.svg | 200 | image/svg+xml | public, max-age=0, must-revalidate | 81ad8e5503b4 = public/ |
| favicon-96x96.png | 200 | image/png | public, max-age=0, must-revalidate | 29903e177cd9 = public/ |
| apple-touch-icon.png | 200 | image/png | public, max-age=0, must-revalidate | 03fe69078c86 = public/ |
| site.webmanifest | 200 | application/manifest+json | public, max-age=0, must-revalidate | a44fab5ad666 = public/ |
| icon-192.png | 200 | image/png | public, max-age=0, must-revalidate | 76c5376b8f47 = public/ |
| icon-512.png | 200 | image/png | public, max-age=0, must-revalidate | 18ad5b7ba665 = public/ |
| icon-maskable-512.png | 200 | image/png | public, max-age=0, must-revalidate | dca61bfc4977 = public/ |
| prim-logo-512.png | 200 | image/png | public, max-age=0, must-revalidate | 18ad5b7ba665 = public/ |
| og-image.png | 200 | image/png | public, max-age=604800 | f4fb1b575982 = public/ |

Aucune redirection (pas d'en-tête `Location`).

### Pages `/` et `/en/`

- Les 6 déclarations sont présentes : `favicon.ico` (16/32/48), `favicon.svg`, `favicon-96x96.png`, `apple-touch-icon`, `site.webmanifest` et `apple-mobile-web-app-title`.
- Aucune data: URI. Le mot-symbole PRIM est présent 2 fois en SVG (en-tête et pied de page).
- `robots` vaut `index, follow`, et le canonical pointe sur la page elle-même.
- JSON-LD : Organization `#prim` avec un logo ImageObject `prim-logo-512.png` de 512×512 et alternateName `["Prim Studio"]` ; WebSite avec le nom « Prim ».
- Le HTML servi est identique octet par octet à `public/`, à l'exception du script injecté par Cloudflare (§7.2).

### Accès de Google aux icônes

Le robots.txt de prod contient `User-agent: *` / `Allow: /`. Aucun `X-Robots-Tag` n'est renvoyé, ni sur les pages ni sur les icônes.

### Favicon servi par Google (indicateur, pas une preuve)

```
$ curl -sS -L -D - "https://www.google.com/s2/favicons?domain=primapp.dev&sz=64"
HTTP/2 301  location: https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&...&url=http://primapp.dev&size=64
HTTP/2 404  content-type: image/png  (726 o, PNG 16×16 : globe par défaut)
```

Le 2026-10-28 à 03:16Z, Google n'avait encore aucun favicon pour primapp.dev. La variante `url=https://primapp.dev` renvoie le même 404.
Revérifié le 2026-10-28 à 21:01Z, environ 18 h après le déploiement : même 404, même image (SHA-256 identique).

Capture fournie par TLILI HAMDI : recherche Google « primapp » le 2026-10-28 à 04:37 (heure de Paris), environ 40 min après le déploiement de la marque.
- primapp.dev arrive en 1er résultat, avec le titre « Prim — applications iOS natives premium ».
- L'icône affichée est le globe par défaut, et le nom de site affiché est « primapp.dev ».
- L'onglet Chrome du site montre déjà le bouclier : le favicon fonctionne côté navigateur.

## 2. Search Console

### 2.1 Demande d'indexation de `/` et `/en/`

Prérequis vérifiés publiquement le 2026-10-28 à 20:54Z :

| Contrôle | `/` | `/en/` |
|---|---|---|
| Statut HTTP | 200, sans redirection | 200, sans redirection |
| Meta robots | `index, follow, max-image-preview:large, max-snippet:-1` | identique |
| `X-Robots-Tag` | absent | absent |
| Canonical | `https://primapp.dev/` | `https://primapp.dev/en/` |
| Sitemap | présente dans `sitemap.xml` (200, `application/xml`, 16 URLs) | présente |
| robots.txt | `Allow: /`, sitemap déclaré | identique |
| `google-site-verification` | présente | présente |

Rien ne bloque l'exploration ni l'indexation de ces deux URLs.

Reste à faire à la main (procédure dans `manual-actions.md`, étape 2) : pour chaque URL, inspecter, lancer « Tester l'URL en direct », puis cliquer sur « Demander une indexation » si le test est concluant. Noter la date, l'état et les messages.

Ce que dit Google (page « Ask Google to recrawl your URLs », §9) :
- « Crawling can take anywhere from a few days to a few weeks. »
- « Requesting a crawl does not guarantee that inclusion in search results will happen instantly or even at all. »
- Il existe un quota de soumissions individuelles, et « requesting a recrawl multiple times for the same URL won't get it crawled any faster. » Une seule demande par URL suffit.

Résultat : à compléter après l'action manuelle (date, état retourné, messages).

### 2.2 Vérifications complémentaires

| Élément | Déjà validé | Reste à faire (manuel) | Capture à fournir | Résultat attendu |
|---|---|---|---|---|
| Propriété | balise `google-site-verification` présente sur `/` et `/en/` | confirmer la validation (Paramètres → Validation de la propriété) | oui | propriété vérifiée |
| Sitemap | 200, 16 URLs, déclaré dans robots.txt | vérifier qu'il est soumis et lu (Indexation → Sitemaps) | oui | sans erreur, 16 URLs découvertes |
| État d'indexation | — | Indexation → Pages | oui | `/` et `/en/` indexées. « Page avec redirection » probable pour les URLs en 307 (§7.1) |
| Canonical retenue | canonicals déclarés vers la page elle-même | inspection de `/` et `/en/`, si déjà indexées | oui | « URL canonique sélectionnée par Google » identique à l'URL déclarée |
| Erreurs d'exploration | 16 pages en 200, aucun blocage robots | Paramètres → Statistiques sur l'exploration | facultative | ni erreur serveur ni blocage |
| Données structurées | JSON-LD valide (§3) | section Améliorations, si présente | si présente | aucune erreur. Un élément « Applications logicielles » non valide est possible pour `/fichechef` (§3.3) |

## 3. Données structurées

### 3.1 Inventaire (HTML servi, 16 pages, 2026-10-28 à 20:54Z)

Format : JSON-LD uniquement, parsable sur les 16 pages. Microdata : 0. RDFa (`vocab`, `typeof`) : 0. Les balises `og:*` utilisent l'attribut `property`, mais ce n'est pas du balisage schema.org.

| Pages | Types |
|---|---|
| `/`, `/en/` | Organization `#prim`, WebSite `#website` |
| `/a-propos/`, `/en/about/` | Person `#person` (sans `image`), Organization |
| `/fichechef/`, `/en/fichechef/` | SoftwareApplication `#app-fichechef`, Organization |
| les 10 autres pages | Organization |

Cohérence avec le contenu :
- Person « TLILI HAMDI » est nommé dans le texte des pages « à propos ».
- Le nom de SoftwareApplication, « FicheChef », est aussi le `<h1>` de la page.
- La description de WebSite reprend la première phrase de la meta description.

### 3.2 validator.schema.org

validator.schema.org (`POST https://validator.schema.org/validate`, paramètre `url`) :

| URL | Erreurs | Avertissements | Contenu détecté |
|---|---|---|---|
| `/` | 0 | 0 | WebSite → publisher Organization → logo ImageObject `prim-logo-512.png` (512×512) |
| `/a-propos/` (avant P3) | 0 | 0 | Person (`image` = `og-image.png`), Organization |
| `/a-propos/` (après P3) | 0 | 0 | Person sans `image`, Organization |
| `/en/about/` (après P3) | 0 | 0 | Person sans `image`, Organization |

### 3.3 Exigences de Google

**Organization** (page « Organization », mise à jour le 2026-09-08) : « There are no required properties ». Pour le logo :
- « The image must be 112x112px, at minimum. »
- format pris en charge par Google Images ;
- « The image URL must be crawlable and indexable. »
- rendu prévu sur fond blanc.

`prim-logo-512.png` est un PNG 512×512, répond 200, n'est pas bloqué, et la tuile est lisible sur fond blanc : **conforme**. Google utilise ce logo « for example in Search results and knowledge panels ».

**SoftwareApplication** (page « Software app », mise à jour le 2026-09-08) : les propriétés requises sont `name`, `offers.price`, et `aggregateRating` ou `review`. FicheChef n'a ni offre ni note, puisque l'app n'est pas publiée. La page n'est donc **pas éligible** au résultat enrichi « Application » : c'est attendu, et il ne faut rien inventer. À la publication : `offers.price` réel (`0` si l'app est gratuite), et uniquement des notes ou avis réels.

**WebSite** : ne produit pas de résultat enrichi, mais sert au nom de site (§8).

Google rappelle : « Google does not guarantee that features that consume structured data will show up in search results. »

Aucune correction requise. Option non appliquée : si Search Console affiche des erreurs « Applications logicielles » pour `/fichechef`, ne plus émettre SoftwareApplication jusqu'à la publication. Décision à prendre à ce moment-là.

### 3.4 Rich Results Test — action manuelle

Procédure dans `manual-actions.md`, étape 4.

| URL | Résultat attendu |
|---|---|
| `https://primapp.dev/` | élément « Organisation » (ou « Logos » selon la version de l'outil) valide, logo `prim-logo-512.png`, 0 erreur. WebSite n'apparaît pas : c'est normal. |
| `https://primapp.dev/fichechef/` | « Organisation » valide. « Applications logicielles » non valide ou absent : attendu (§3.3). |

Résultat : à compléter.

## 4. Aperçus sociaux (Facebook et LinkedIn)

### 4.1 Balises (HTML servi, 2026-10-28 à 20:54Z)

| Balise | `/` | `/en/` |
|---|---|---|
| `og:title` (= `<title>`) | Prim — applications iOS natives premium | Prim — premium native iOS apps |
| `og:url` (= canonical) | `https://primapp.dev/` | `https://primapp.dev/en/` |
| `og:type` | `website` | `website` |
| `og:site_name` | Prim | Prim |
| `og:locale` / `og:locale:alternate` | `fr_FR` / `en_US` | `en_US` / `fr_FR` |
| `og:image` | `https://primapp.dev/og-image.png`, 1200×630 | identique |
| `og:image:alt` | « Logo Prim : bouclier monogramme et mot-symbole PRIM, en or sur fond sombre » | « Prim logo: monogram shield and PRIM wordmark in gold on a dark background » |
| `twitter:card` | `summary_large_image` | identique |
| `twitter:title`, `twitter:description`, `twitter:image` | identiques aux `og:*` | identiques aux `og:*` |

`og:description` est identique à la meta description :
- `/` : « Prim, studio indépendant d'applications iOS natives premium pour les pros et la conformité française. Offline, accessibles, privacy-first. Découvrez FicheChef et les apps du studio. »
- `/en/` : « Prim, an independent studio building premium native iOS apps for professionals and French compliance. Offline, accessible, privacy-first. Discover FicheChef and the studio's apps. »

Sur les 16 pages, tout est présent et cohérent : `og:url` identique au canonical, `og:title`, `og:description`, `og:image` en https en 1200×630 avec alt, `og:type`, `og:site_name`, `og:locale`, `twitter:card`, meta robots `index`. Aucune anomalie.

### 4.2 Image

`og-image.png` : 200, `image/png`, 1200×630 (ratio 1,91:1), 61 153 octets, SHA identique à `public/` (§1), `Cache-Control: public, max-age=604800`.

### 4.3 Accès des robots (indicatif)

Avec les user-agents facebookexternalhit, LinkedInBot et Googlebot, simulés depuis une IP non vérifiée : réponse 200 avec `og:image`. La détection anti-bot de Cloudflare (§7.2) ne bloque pas ces requêtes. À confirmer manuellement avec les outils officiels, qui appellent depuis leurs propres IP.

### 4.4 Contrôles manuels

Les deux vérifications de chaque outil portent sur `/` et `/en/`. Procédure dans `manual-actions.md`, étapes 5 et 6.

- **Facebook Sharing Debugger** : « Récupérer à nouveau » sur chaque URL. Attendu : code 200 et la nouvelle image (fond sombre, bouclier + PRIM or). L'avertissement `fb:app_id` est sans objet : le site n'a pas d'application Facebook.
- **LinkedIn Post Inspector** : chaque inspection force un nouveau scrape. Attendu : la nouvelle image et « Last scraped » à la date du jour.
- `og-image.png` garde la même URL : seul un nouveau scrape forcé vide le cache de ces plateformes. Si l'ancienne image persiste, relancer une fois quelques minutes plus tard. En dernier recours, publier l'image sous une nouvelle URL, ce qui modifie le site et demande ton accord.

Anomalie : aucune. Correctif : aucun. Résultats : à compléter.

## 5. Person.image (P3) — vérifié

`image` pointait vers `og-image.png`, qui montre le logo Prim depuis la nouvelle identité. Le JSON-LD déclarait donc le logo comme photo de TLILI HAMDI. Option retenue : supprimer la propriété, qui est facultative pour `Person`, car aucun portrait n'est publié.

- Commit `2fe1d46` (`fix(seo): retire Person.image, qui pointait vers l'og-image de marque`) :
  - `scripts/lib/jsonld.mjs` : la ligne est remplacée par un commentaire qui explique l'absence d'image ;
  - `public/a-propos/index.html` et `public/en/about/index.html` : régénérés par le build, une ligne en moins chacun.
- `npm run validate` : verify 92 contrôles OK, verify:brand 321 contrôles OK, html-validate 0 erreur, gate a11y 0 violation WCAG 2 AA sur 16 routes.
- Push `2a16239..2fe1d46`, visible en prod environ 30 s plus tard (03:29:46Z).
  - Sur `/a-propos/` et `/en/about/`, `Person` n'a plus d'`image` et Organization est intacte.
  - validator.schema.org : 0 erreur, 0 avertissement (§3).

## 6. Always Use HTTPS et P4

### 6.1 État (2026-10-28 à 20:54Z)

| Requête | Réponse | Verdict |
|---|---|---|
| `https://primapp.dev/` | 200 (HTTP/2, TLS 1.3) | OK |
| `http://primapp.dev/` | 200, sans redirection | Non conforme |
| `https://www.primapp.dev/` | 301 → `https://primapp.dev/` | OK |
| `http://www.primapp.dev/` | 301 → `http://primapp.dev/` (on reste en HTTP) | Non conforme |

- **Boucles de redirection** : aucune. Au plus 1 redirection (`curl -L --max-redirs 5`), réponse finale 200.
- **Certificat** (`openssl s_client`) :
  - CN `primapp.dev`, SAN `primapp.dev`, `www.primapp.dev` et `*.www.primapp.dev` ;
  - émetteur Google Trust Services (WE1), valide du 2026-10-06 au 2027-01-04 ;
  - renouvellement géré par Cloudflare : à confirmer manuellement dans le dashboard.
- **HSTS** `max-age=31536000; includeSubDomains`, et **CSP** avec `upgrade-insecure-requests`. Ces deux protections ne jouent que pour un visiteur déjà venu en HTTPS : elles ne couvrent pas une première visite en HTTP.
- **Liens internes** : aucun lien absolu en `http://` sur les 16 pages.

**Statut : partiellement conforme.** HTTPS, certificat, HSTS, redirection www → domaine sans www et liens internes sont conformes. Il manque la redirection HTTP → HTTPS.

### 6.2 Correctif — action manuelle

Cloudflare → zone primapp.dev → SSL/TLS → Edge Certificates → « Always Use HTTPS » sur On (`manual-actions.md`, étape 1). Aucun changement de code. Le réglage s'applique à toute la zone, donc aussi à `www`.

Attendu après activation, à confirmer par la revérification :
- `http://primapp.dev/` → 301 → `https://primapp.dev/` ;
- `http://www.primapp.dev/` → 301 → `https://www.primapp.dev/` → 301 → `https://primapp.dev/`.

```
curl -sS -o /dev/null -w '%{http_code} → %{redirect_url}\n' http://primapp.dev/
curl -sS -L --max-redirs 5 -o /dev/null -w 'final=%{url_effective} redirections=%{num_redirects}\n' http://www.primapp.dev/
```

Résultat après activation : à compléter.

### 6.3 Constat initial, Wrangler et branches

- **HTTPS** : à 03:16Z, `curl -sI http://primapp.dev/` renvoyait déjà `HTTP/1.1 200 OK`, sans 301.
- **Wrangler** : le jeton a expiré, `npx wrangler login` est proposé. `workers_dev: false` garantit qu'aucune URL workers.dev ne sera créée.
- **Branches** : `git branch -d feat/brand-logo refonte/studio-first`. Elles étaient à `2a16239` et `65d2c95`, toutes deux fusionnées dans `main` (`git branch --merged main`) et sans copie sur le dépôt distant. `backup-stack-edit-erronе` n'est pas fusionnée : elle est conservée.

## 7. Constats hors périmètre (non corrigés)

### 7.1 Redirections 307 sur 14 des 16 URLs du sitemap

Toutes les URLs du sitemap sauf `/` et `/en/` répondent `307` vers leur version avec slash final (`/a-propos` → `/a-propos/`). Pourtant, le canonical, les hreflang, le sitemap, les liens internes et `Person.url` pointent tous vers la version sans slash. Google reçoit donc des signaux contradictoires, et Search Console signalera probablement ces URLs en « Page avec redirection ».

- **Cause** : `content/routes.js:76-79` (`outputPathFor`) génère `x/index.html`. Avec `html_handling: "auto-trailing-slash"`, Cloudflare le sert en `/x/` et redirige `/x` en 307. Le problème date de `111287a` (2026-06-17).
- **Impact sur P1** : aucun, `/` et `/en/` répondent 200.
- **Correctif proposé**, dans une mission dédiée :
  - générer `x.html` (servi en `/x` avec un 200) pour toutes les routes sauf `/` et `/en/` ;
  - supprimer les anciens dossiers de sortie ;
  - lancer `npm run validate` et revérifier les 16 URLs.

### 7.2 Script injecté par Cloudflare

Cloudflare insère un script juste avant `</body>` sur chaque page HTML (`window.__CF$cv$params`, chargement de `/cdn-cgi/challenge-platform/scripts/jsd/main.js`, détections JavaScript anti-bot). Ce script retiré, le HTML de prod est identique à `public/` (vérifié sur `/`, `/en/`, `/a-propos/` et `/en/about/`). La CSP l'autorise : script inline, ressource sur la même origine.

À vérifier : la page confidentialité affirme « Aucun cookie n'est déposé par le site lui-même ». Si ce mécanisme dépose un cookie avant tout clic sur Calendly, cette phrase devient inexacte. Non vérifié ici : il faut un contrôle dans le navigateur (DevTools → Application → Cookies).

### 7.3 Homonymie (pour information)

Sur la même recherche « primapp », l'Aperçu IA de Google présente d'abord PRIM'APP : une application de RFS Consultants pour le catalogue de bandes transporteuses PROVULCO, présente sur Google Play et l'App Store. Il cite à part « Prim : un studio de création d'applications iOS natives créé par Tlili Hamdi (primapp.dev) ». Google distingue donc déjà les deux entités. Rien à corriger : cela confirme l'intérêt de l'Organization `#prim` et de la règle « aucun PrimApp » contrôlée par verify:brand.

## 8. Revérification du favicon dans Google

J = date de la demande d'indexation (§2). Si elle est faite le 2026-10-28 :

- **J+7 : 2026-11-04**
- **J+21 : 2026-11-18**

```
curl -sS -L -o s2.png -w '%{http_code}\n' "https://www.google.com/s2/favicons?domain=primapp.dev&sz=64"
```

Attendu : `200` et le bouclier Prim. Un `404` signifie que Google affiche toujours le globe par défaut. À compléter par une recherche `site:primapp.dev` sur mobile. Google ne garantit aucun délai de mise à jour.

Vérifier aussi le nom de site affiché : « Prim » est attendu, « primapp.dev » était affiché le 28/10. Google peut garder le domaine s'il juge « Prim » trop ambigu (voir §7.3). À réévaluer à J+21.

Si la demande d'indexation est faite le 2026-10-29 : J+7 = 2026-11-05 et J+21 = 2026-11-19.

**Conformité aux consignes Google** (page « Favicons », mise à jour le 2026-10-27) :
- `<link rel="icon">` déclaré sur la page d'accueil : oui.
- Google exige un favicon « square (1:1 aspect ratio) that's at least 8x8px » et en recommande un « larger than 48x48px » : le PNG fait 96×96 et l'ICO va jusqu'à 48×48.
- Formats acceptés : « BMP, GIF, ICO, PNG, JPEG, PPM, and TIFF ». Le SVG n'y figure pas. Ce n'est pas bloquant : l'ICO et le PNG déclarés sont dans la liste.
- Googlebot (page d'accueil) et Googlebot-Image (fichier) ne sont pas bloqués : robots.txt `Allow: /`, pas de `X-Robots-Tag`.
- URL stable : oui.
- Google précise : « A favicon isn't guaranteed to appear in Google Search results, even if all guidelines are met. » Le délai est celui d'une exploration : « crawling can take anywhere from several days to several weeks ».

**Nom de site** (page « Site names ») : Google « generally tries to use a preferred site name from `WebSite` structured data », mais peut afficher le domaine. `alternateName` (« Prim Studio ») lui donne déjà une autre option. Si « primapp.dev » reste affiché à J+21, la page propose ensuite d'ajouter le domaine comme `alternateName` de secours. Prendre le domaine comme nom principal n'est conseillé qu'en dernier recours. La décision te revient.

**Automatisation** : je propose une routine `/schedule` qui contrôle le favicon s2 à J+7 et à J+21. Elle ne sera créée qu'avec ton accord. Les recherches Google et Search Console restent manuelles (`manual-actions.md`, étape 8).

## 9. Sources

- Google Search Central — [Organization structured data](https://developers.google.com/search/docs/appearance/structured-data/organization) (mise à jour le 2026-09-08)
- Google Search Central — [Software app structured data](https://developers.google.com/search/docs/appearance/structured-data/software-app) (2026-09-08)
- Google Search Central — [Ask Google to recrawl your URLs](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl) (2025-12-10)
- Google Search Central — [Favicons in Google Search](https://developers.google.com/search/docs/appearance/favicon-in-search) (2026-10-27)
- Google Search Central — [Site names in Google Search](https://developers.google.com/search/docs/appearance/site-names) (2025-12-10)

— TLILI HAMDI
