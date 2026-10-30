# Actions manuelles — suivi de l'identité Prim (primapp.dev)

| | |
|---|---|
| Auteur | TLILI HAMDI |
| Date | 2026-10-28 |
| Référence | `RAPPORT-identite-prim.md` (fait foi), `seo-checklist-results.md` |

Ce fichier ne contient que les actions qui passent par tes comptes : Google, Facebook, LinkedIn et Cloudflare. Tout le reste a déjà été vérifié automatiquement.

Ordre conseillé : HTTPS d'abord, pour que Google réexplore un site qui redirige déjà ; puis Search Console ; puis les outils de test.

Pour le retour, une ligne suffit (par exemple « HTTPS fait, SC ok ×2, RRT ok, FB ok ×2, LI ok ×2 »), accompagnée des captures listées en fin de fichier.

## 1. Cloudflare — Always Use HTTPS (30 s)

1. Ouvrir https://dash.cloudflare.com/?to=/:account/:zone/ssl-tls/edge-certificates et choisir la zone primapp.dev. À défaut : zone primapp.dev → SSL/TLS → Edge Certificates.
2. Mettre « Always Use HTTPS » sur On.

- **Attendu** : `http://primapp.dev/` → 301 → `https://primapp.dev/`. Je le vérifie par curl.
- **À fournir** : « HTTPS fait ». La capture de l'interrupteur est facultative.

## 2. Search Console — test en direct et demande d'indexation (3 min)

Ouvrir https://search.google.com/search-console, propriété primapp.dev. Faire les étapes suivantes pour `https://primapp.dev/`, puis pour `https://primapp.dev/en/` :

1. Coller l'URL dans la barre « Inspecter n'importe quelle URL ».
2. Cliquer sur « Tester l'URL en direct ».
3. Si « L'URL est disponible pour Google » s'affiche avec Exploration autorisée « Oui », Récupération de page « Réussie » et Indexation autorisée « Oui », cliquer sur « Demander une indexation ». Sinon, s'arrêter et m'envoyer la capture.
4. Noter la date, l'état et le message affiché (« Indexation demandée »).

Une seule demande par URL suffit : il existe un quota, et répéter la demande n'accélère rien.

- **À fournir**, pour chaque URL : la capture du bloc « Disponibilité de la page » du test en direct, et la confirmation « Indexation demandée ».

## 3. Search Console — contrôles complémentaires (3 min)

| Écran | Chemin | Résultat attendu | Capture |
|---|---|---|---|
| Propriété | Paramètres → Validation de la propriété | propriété vérifiée | oui |
| Sitemap | Indexation → Sitemaps | `sitemap.xml` sans erreur, 16 URLs découvertes. S'il n'est pas soumis, ajouter `sitemap.xml`. | oui |
| Pages | Indexation → Pages | `/` et `/en/` indexées. Noter le nombre de « Page avec redirection » (lié aux 307). | oui |
| Canonical | inspection de `/` et de `/en/` → Indexation de la page (si déjà indexées) | « URL canonique sélectionnée par Google » identique à l'URL déclarée | oui |
| Exploration | Paramètres → Statistiques sur l'exploration | ni erreur serveur ni blocage | facultative |
| Données structurées | Améliorations (menu de gauche), si la section existe | aucune erreur. « Applications logicielles » peut apparaître comme non valide pour `/fichechef` : c'est attendu. | si présente |

## 4. Test des résultats enrichis (1 min)

- **`/`** : https://search.google.com/test/rich-results?url=https%3A%2F%2Fprimapp.dev%2F
  - Attendu : « Organisation » (ou « Logos ») valide, logo `prim-logo-512.png`, 0 erreur.
  - WebSite n'apparaît pas : c'est normal.
- **`/fichechef/`** : https://search.google.com/test/rich-results?url=https%3A%2F%2Fprimapp.dev%2Ffichechef%2F
  - Attendu : « Organisation » valide.
  - « Applications logicielles » non valide ou absent : c'est attendu, car il n'y a ni prix ni note tant que l'app n'est pas publiée.
- **À fournir** : la capture du résumé de chaque test.

## 5. Facebook Sharing Debugger (1 min)

1. Ouvrir https://developers.facebook.com/tools/debug/?q=https%3A%2F%2Fprimapp.dev%2F, puis https://developers.facebook.com/tools/debug/?q=https%3A%2F%2Fprimapp.dev%2Fen%2F
2. Pour chaque URL, cliquer sur « Récupérer à nouveau ».

- **Attendu** : code de réponse 200, et un aperçu avec la nouvelle image (fond sombre, bouclier + PRIM or), le titre et la description de la page. L'avertissement `fb:app_id` est sans objet.
- Si l'ancienne image reste affichée, cliquer une seconde fois sur « Récupérer à nouveau » quelques minutes plus tard.
- **À fournir** : la capture de l'aperçu pour chaque URL.

## 6. LinkedIn Post Inspector (1 min)

1. Ouvrir https://www.linkedin.com/post-inspector/
2. Inspecter `https://primapp.dev/`, puis `https://primapp.dev/en/`.

- **Attendu** : la nouvelle image, le titre et la description de la page, et une date « Last scraped » du jour. L'inspection force un nouveau scrape.
- **À fournir** : la capture de l'aperçu pour chaque URL.

## 7. Facultatif — cookies (hors périmètre, rapport §7.2)

Ouvrir https://primapp.dev/ en navigation privée, sans cliquer sur Calendly, puis DevTools → Application → Cookies → `https://primapp.dev`.

- **Attendu**, si la page confidentialité dit vrai : aucun cookie. Sinon, noter le nom et le domaine de chaque cookie.

## 8. Revérifications à J+7 et J+21

J = jour de la demande d'indexation (étape 2) :
- demande faite le 2026-10-28 : J+7 = **2026-11-04**, J+21 = **2026-11-18** ;
- demande faite le 2026-10-29 : J+7 = 2026-11-05, J+21 = 2026-11-19.

À chaque date :
- Faire les recherches Google « primapp » et `site:primapp.dev`, sur mobile et sur ordinateur. Attendu : le bouclier comme favicon et « Prim » comme nom de site.
- Vérifier dans Search Console l'état d'indexation de `/` et `/en/`.
- **À fournir** : les captures des résultats.

Le contrôle public du favicon (s2) peut être automatisé par une routine `/schedule`. Elle ne sera créée qu'avec ton accord.

## Captures à fournir

1. Search Console : le test en direct et la confirmation « Indexation demandée », pour `/` et `/en/`.
2. Search Console : propriété, sitemaps, rapport Pages, canonical, et Améliorations si la section existe.
3. Test des résultats enrichis : `/` et `/fichechef/`.
4. Facebook : `/` et `/en/`.
5. LinkedIn : `/` et `/en/`.
6. À J+7 et J+21 : les résultats de recherche Google.

— TLILI HAMDI
