# Résultats de la checklist SEO — primapp.dev

| | |
|---|---|
| Auteur | TLILI HAMDI |
| Date | 2026-10-28 (contrôles à 20:54Z et 21:01Z) |
| Référence | `RAPPORT-identite-prim.md` fait foi ; ce fichier en est l'index, un contrôle par ligne |

Statut : **OK**, **À corriger** ou **Action manuelle requise**.
Responsable :
- *Automatisable* : contrôle ou correctif que je peux faire, avec ton accord pour toute modification ;
- *Manuel* : action dans l'un de tes comptes.

## Indexation et Search Console

| # | Contrôle | Statut | Méthode | Résultat observé | Preuve | Action correctrice | Responsable |
|---|---|---|---|---|---|---|---|
| 1 | `/` et `/en/` accessibles | OK | curl | 200 `text/html`, aucune redirection | rapport §2.1 | — | Automatisable |
| 2 | Meta robots | OK | analyse HTML | `index, follow, max-image-preview:large, max-snippet:-1` | rapport §2.1 | — | Automatisable |
| 3 | `X-Robots-Tag` | OK | en-têtes, 16 pages | absent | rapport §2.1 | — | Automatisable |
| 4 | Canonical | OK | analyse HTML | pointe sur la page elle-même (`/`, `/en/`) | rapport §2.1 | — | Automatisable |
| 5 | robots.txt | OK | curl | `Allow: /`, sitemap déclaré | rapport §2.1 | — | Automatisable |
| 6 | Sitemap | OK | curl | 200 `application/xml`, 16 URLs, dont `/` et `/en/` | rapport §2.1 | — | Automatisable |
| 7 | Balise de validation Search Console | OK | analyse HTML | `google-site-verification` présente sur `/` et `/en/` | rapport §2.1 | — | Automatisable |
| 8 | Test en direct et demande d'indexation de `/` et `/en/` | Action manuelle requise | Search Console | à faire | — | `manual-actions.md` §2 | Manuel |
| 9 | Propriété, sitemap soumis, rapport Pages, canonical retenue, exploration, améliorations | Action manuelle requise | Search Console | à confirmer manuellement | — | `manual-actions.md` §3 | Manuel |
| 10 | Redirections 307 sur 14 URLs du sitemap | À corriger | curl, 16 URLs | 307 vers la version avec slash | rapport §7.1 | `content/routes.js:76-79` : générer `x.html` (mission dédiée, diff montré avant) | Automatisable |

## Données structurées

| # | Contrôle | Statut | Méthode | Résultat observé | Preuve | Action correctrice | Responsable |
|---|---|---|---|---|---|---|---|
| 11 | Formats présents | OK | analyse HTML, 16 pages | JSON-LD uniquement ; Microdata 0 ; RDFa 0 | rapport §3.1 | — | Automatisable |
| 12 | JSON-LD parsable | OK | `JSON.parse`, 16 pages | 16/16 | rapport §3.1 | — | Automatisable |
| 13 | validator.schema.org | OK | API du validateur | 0 erreur, 0 avertissement (`/`, `/a-propos/`, `/en/about/`) | rapport §3.2 | — | Automatisable |
| 14 | Logo Organization face aux exigences Google | OK | comparaison avec la doc Google | PNG 512×512 (minimum 112×112), 200, explorable | rapport §3.3 | — | Automatisable |
| 15 | `Person.image` | OK | analyse HTML et validateur | retirée (`2fe1d46`), en prod | rapport §5 | — | Automatisable |
| 16 | SoftwareApplication de `/fichechef` | OK | comparaison avec la doc Google | ni `offers` ni `aggregateRating`/`review` : non éligible au résultat enrichi « Application », comme prévu | rapport §3.3 | aucune maintenant ; à la publication, prix et notes réels uniquement | Automatisable |
| 17 | Rich Results Test sur `/` et `/fichechef/` | Action manuelle requise | outil Google | à faire | — | `manual-actions.md` §4 | Manuel |

## Facebook et LinkedIn

| # | Contrôle | Statut | Méthode | Résultat observé | Preuve | Action correctrice | Responsable |
|---|---|---|---|---|---|---|---|
| 18 | Balises Open Graph et Twitter (16 pages) | OK | analyse HTML | `og:url` = canonical, `og:title` = `<title>`, `og:description` = description, type, site_name, locale, image 1200×630 avec alt, `summary_large_image` | rapport §4.1 | — | Automatisable |
| 19 | `og-image.png` | OK | curl et SHA-256 | 200, `image/png`, 1200×630, 61 153 octets, identique à `public/`, cache 7 jours | rapport §4.2 | — | Automatisable |
| 20 | Accès des robots (user-agents simulés) | OK | `curl -A` | 200 avec `og:image` pour facebookexternalhit, LinkedInBot et Googlebot (indicatif) | rapport §4.3 | — | Automatisable |
| 21 | `fb:app_id` | OK | analyse HTML | absent : l'avertissement Facebook est sans objet | rapport §4.4 | — | Automatisable |
| 22 | Facebook Sharing Debugger sur `/` et `/en/` | Action manuelle requise | outil Facebook | à faire | — | `manual-actions.md` §5 | Manuel |
| 23 | LinkedIn Post Inspector sur `/` et `/en/` | Action manuelle requise | outil LinkedIn | à faire | — | `manual-actions.md` §6 | Manuel |

## HTTPS

| # | Contrôle | Statut | Méthode | Résultat observé | Preuve | Action correctrice | Responsable |
|---|---|---|---|---|---|---|---|
| 24 | `https://primapp.dev/` | OK | curl, openssl | 200, HTTP/2, TLS 1.3 | rapport §6.1 | — | Automatisable |
| 25 | `http://primapp.dev/` vers HTTPS | À corriger | curl | 200, aucune redirection | rapport §6.1 | Always Use HTTPS (`manual-actions.md` §1), puis vérification du 301 | Manuel pour le correctif, automatisable pour la vérification |
| 26 | `http://www.primapp.dev/` | À corriger | curl | 301 vers `http://primapp.dev/` : on reste en HTTP | rapport §6.1 | même réglage que le n° 25 | Manuel pour le correctif, automatisable pour la vérification |
| 27 | `https://www` vers le domaine sans www | OK | curl | 301 vers `https://primapp.dev/` | rapport §6.1 | — | Automatisable |
| 28 | Boucles de redirection | OK | `curl -L --max-redirs 5` | au plus 1 redirection, réponse finale 200 | rapport §6.1 | — | Automatisable |
| 29 | Certificat | OK | `openssl s_client` | couvre primapp.dev et www, émis par Google Trust Services WE1, valide jusqu'au 2027-01-04 | rapport §6.1 | renouvellement automatique par Cloudflare : à confirmer manuellement | Automatisable |
| 30 | HSTS et `upgrade-insecure-requests` | OK | en-têtes | `max-age=31536000; includeSubDomains` | rapport §6.1 | — | Automatisable |
| 31 | Liens internes absolus en `http://` | OK | analyse HTML, 16 pages | 0 | rapport §6.1 | — | Automatisable |

## Affichage dans Google

| # | Contrôle | Statut | Méthode | Résultat observé | Preuve | Action correctrice | Responsable |
|---|---|---|---|---|---|---|---|
| 32 | Favicon dans Google | Action manuelle requise | curl s2 et recherche | 404 avec le globe par défaut (03:16Z et 21:01Z) | rapport §1 et §8 | demande d'indexation (`manual-actions.md` §2), puis revérification à J+7 et J+21 | Manuel pour la recherche, automatisable pour s2 |
| 33 | Nom de site | Action manuelle requise | recherche Google (capture) | « primapp.dev » au lieu de « Prim » | rapport §8 | revérifier à J+21 ; si rien ne change, appliquer les options de la doc Google | Manuel |
| 34 | Consignes Google pour le favicon | OK | comparaison avec la doc Google | déclaré sur la page d'accueil, carré, PNG 96×96, ICO, robots non bloqués. Le SVG n'est pas un format listé, sans conséquence. | rapport §8 | — | Automatisable |
| 35 | Cookies et page confidentialité (hors périmètre) | Action manuelle requise | DevTools | à confirmer manuellement | rapport §7.2 | `manual-actions.md` §7 | Manuel |

## Prochaines vérifications

J = jour de la demande d'indexation.
- Demande faite le 2026-10-28 : J+7 = **2026-11-04**, J+21 = **2026-11-18**.
- Demande faite le 2026-10-29 : J+7 = 2026-11-05, J+21 = 2026-11-19.

— TLILI HAMDI
