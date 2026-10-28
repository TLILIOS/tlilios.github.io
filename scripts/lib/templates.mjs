// scripts/lib/templates.mjs — Composants de rendu sans framework (template literals).
// Toute chaîne UI vient des données (site.json / pages). a11y AA dès le commit.

import { buildGraph, renderJsonLd } from "./jsonld.mjs";
import { wordmark } from "./brand.mjs";

// ---------- échappement ----------
const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
export const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ESC[c]);
// `raw` : contenu de données contenant du HTML inline VOULU (ex <strong>, <a>) — déjà maîtrisé,
// provient de nos fichiers content/, pas d'entrée utilisateur.
export const raw = (s) => String(s == null ? "" : s);

// ---------- CSS partagé (un seul fichier inline, déterministe) ----------
// Tokens couleur vérifiés contre #08090c (cf. ADR-0003 / pa11y gate).
export { SITE_CSS } from "./styles.mjs";

// ---------- <head> ----------
export function head({ site, config, lang, route, pageMeta, jsonldType, app }) {
  const s = site[lang];
  const { SITE_URL, X_DEFAULT } = config;
  const selfPath = route[lang];
  const canonical = `${SITE_URL}${selfPath === "/" ? "/" : selfPath}`;
  const frUrl = `${SITE_URL}${route.fr}`;
  const enUrl = `${SITE_URL}${route.en}`;
  const xDefaultUrl = X_DEFAULT === "en" ? enUrl : frUrl;

  // Suffixe « | Prim » ajouté sauf si le title le porte déjà (pages légales migrées)
  // ou s'il commence déjà par la marque (évite « Prim — … | Prim »).
  const rawTitle = pageMeta.title || s.brand;
  const alreadyBranded =
    pageMeta.titleHasSuffix ||
    rawTitle.includes(s.meta.titleSuffix.trim()) ||
    rawTitle.startsWith(s.brand);
  const title = esc(alreadyBranded ? rawTitle : rawTitle + s.meta.titleSuffix);
  const description = esc(pageMeta.description || s.meta.defaultDescription);
  const ogType = pageMeta.ogType || "website";
  const ogLocale = lang === "fr" ? "fr_FR" : "en_US";
  const ogLocaleAlt = lang === "fr" ? "en_US" : "fr_FR";

  const graph = buildGraph({ type: jsonldType, SITE_URL, lang, app });

  return `<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="google-site-verification" content="G0pLsmY4YS0TQz-5fA_5gghXjHHnqBGh0Mmuv5CLERg">
<title>${title}</title>
<meta name="description" content="${description}">
<meta name="author" content="TLILI HAMDI">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="theme-color" content="${esc(s.meta.themeColor)}">
<meta name="color-scheme" content="dark">
<link rel="canonical" href="${esc(canonical)}">
<link rel="alternate" hreflang="fr" href="${esc(frUrl)}">
<link rel="alternate" hreflang="en" href="${esc(enUrl)}">
<link rel="alternate" hreflang="x-default" href="${esc(xDefaultUrl)}">
<link rel="icon" href="/favicon.ico" sizes="16x16 32x32 48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-96x96.png" type="image/png" sizes="96x96">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="apple-mobile-web-app-title" content="Prim">
<link rel="dns-prefetch" href="https://github.com">
<meta property="og:type" content="${esc(ogType)}">
<meta property="og:site_name" content="${esc(s.meta.ogSiteName)}">
<meta property="og:title" content="${title}">
<meta property="og:description" content="${description}">
<meta property="og:url" content="${esc(canonical)}">
<meta property="og:locale" content="${ogLocale}">
<meta property="og:locale:alternate" content="${ogLocaleAlt}">
<meta property="og:image" content="${SITE_URL}/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="${esc(s.meta.ogImageAlt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${title}">
<meta name="twitter:description" content="${description}">
<meta name="twitter:image" content="${SITE_URL}/og-image.png">
${renderJsonLd(graph)}
<link rel="stylesheet" href="/assets/site.css">`;
}

// ---------- switcher de langue : TEXTE « FR / EN », zéro drapeau, liens hreflang/lang ----------
export function langSwitcher({ site, lang, route }) {
  const s = site[lang];
  const ls = s.langSwitch;
  const frHref = route.fr;
  const enHref = route.en;
  const optFr =
    lang === "fr"
      ? `<span class="lang-opt" aria-current="page" lang="fr">${esc(ls.fr)}</span>`
      : `<a class="lang-opt" href="${esc(frHref)}" hreflang="fr" lang="fr" aria-label="${esc(ls.toFrAria)}">${esc(ls.fr)}</a>`;
  const optEn =
    lang === "en"
      ? `<span class="lang-opt" aria-current="page" lang="en">${esc(ls.en)}</span>`
      : `<a class="lang-opt" href="${esc(enHref)}" hreflang="en" lang="en" aria-label="${esc(ls.toEnAria)}">${esc(ls.en)}</a>`;
  return `<div class="lang-switch" role="group" aria-label="${esc(ls.aria)}">
  ${optFr}<span class="lang-sep" aria-hidden="true">/</span>${optEn}
</div>`;
}

// ---------- header / nav ----------
export function header({ site, lang, route }) {
  const s = site[lang];
  const homeHref = lang === "fr" ? "/" : "/en/";
  const items = s.nav.items
    .map((it) => `<li><a href="${esc(it.href)}">${esc(it.label)}</a></li>`)
    .join("\n      ");
  return `<header>
<nav aria-label="${esc(s.nav.aria)}">
  <a href="${homeHref}" class="nav-logo" aria-label="${esc(s.nav.logoAria)}">${wordmark({ fontPx: 22.4, decorative: true })}</a>
  <div class="nav-right">
    <ul class="nav-links">
      ${items}
    </ul>
    ${langSwitcher({ site, lang, route })}
  </div>
</nav>
</header>`;
}

// ---------- footer ----------
export function footer({ site, lang }) {
  const s = site[lang];
  const links = s.footer.links
    .map((l) => `<a href="${esc(l.href)}">${esc(l.label)}</a>`)
    .join("\n    ");
  return `<footer>
  <div class="footer-brand">${wordmark({ fontPx: 14.4, decorative: false })} — Craft at prime.</div>
  <nav class="footer-links" aria-label="${esc(s.footer.legalNavAria)}">
    ${links}
  </nav>
  <div class="footer-copy">${esc(s.footer.copy)}</div>
</footer>`;
}

// ---------- CTA status-aware (surface studio vs freelance encodée par role/kind) ----------
// Retourne le bouton approprié pour une app selon son status (anti-faux-lien).
export function appCtaButton({ app, site, lang, primary = true }) {
  const cta = site[lang].cta;
  const cls = primary ? "btn-primary" : "btn-ghost";
  if (app.appStoreUrl && app.status === "available") {
    return `<a class="${cls}" href="${esc(app.appStoreUrl)}" rel="noopener">${esc(cta.appStore)}</a>`;
  }
  if (app.testflightUrl) {
    return `<a class="${cls}" href="${esc(app.testflightUrl)}" rel="noopener">${esc(cta.testflight)}</a>`;
  }
  // Pas d'URL → état honnête « Bientôt », non cliquable (span), jamais de faux lien.
  return `<span class="${cls} is-disabled" aria-disabled="true">${esc(cta.comingSoon)}</span>`;
}

// Badge de statut lisible (status-aware).
export function statusBadge({ app, lang }) {
  const labels = {
    available: { fr: "Disponible", en: "Available" },
    "coming-soon": { fr: "Bientôt", en: "Coming soon" },
    "in-development": { fr: "En développement", en: "In development" },
    concept: { fr: "En conception", en: "Concept" },
  };
  const l = (labels[app.status] || labels.concept)[lang];
  return `<span class="status-badge status-${esc(app.status)}">${esc(l)}</span>`;
}

// Carte app pour la grille home.
export function appCard({ app, site, lang }) {
  const tagline = app.tagline[lang];
  const flagshipMark = app.flagship
    ? `<span class="app-card-flagship">${lang === "fr" ? "Phare" : "Flagship"}</span>`
    : "";
  // Lien « Découvrir <App> » uniquement pour le flagship qui a une page produit dédiée.
  // Nom accessible spécifique (évite la collision SC 2.4.4 avec le CTA de la section flagship).
  const detailLink = app.flagship
    ? `<a class="app-card-link" href="${lang === "fr" ? "/fichechef" : "/en/fichechef"}">${lang === "fr" ? "Découvrir" : "Discover"} ${esc(app.name)} →</a>`
    : "";
  return `<article class="app-card">
  <div class="app-card-head">
    <h3 class="app-card-name">${esc(app.name)}</h3>
    ${statusBadge({ app, lang })}${flagshipMark}
  </div>
  <p class="app-card-category">${esc(app.category)}</p>
  <p class="app-card-tagline">${esc(tagline)}</p>
  ${detailLink}
</article>`;
}

// ---------- carte projet (démo portfolio fondateur) ----------
// iPhone-frame = bouton ouvrant la modale vidéo (AA). Vidéo inline muette, lecture au clic.
export function projectCard({ project: pr, i18n, lang }) {
  const tag = pr.tag[lang];
  const desc = pr.desc[lang];
  const trainingBadge = pr.training
    ? `<span class="project-badge">${esc(i18n.trainingBadge)}</span>`
    : "";
  const tech = pr.tech.map((t) => `<span class="tech-tag">${esc(t)}</span>`).join("");
  const links = pr.links
    .map((l) => {
      // Liens externes (http…) en nouvel onglet ; liens internes (/fichechef) dans le même
      // onglet, préfixés /en sur les pages anglaises pour rester dans la bonne locale.
      const external = /^https?:/i.test(l.href);
      const href = !external && lang === "en" ? `/en${l.href}` : l.href;
      const attrs = external ? ` target="_blank" rel="noopener noreferrer"` : "";
      return `<a class="project-link" href="${esc(href)}"${attrs} aria-label="${esc(l.aria[lang])}">${esc(l.label[lang])}</a>`;
    })
    .join("");
  // Légende visible localisée (T2). Démos muettes sans audio : la figcaption suffit.
  const caption = `${i18n.captionPrefix} ${pr.name}`;
  return `<article class="project-card">
  <figure class="project-visual">
    <button type="button" class="iphone-frame" aria-haspopup="dialog" aria-label="${esc(i18n.zoomAria)} ${esc(pr.name)}" data-video-src="${esc(pr.video)}" data-video-poster="${esc(pr.poster)}" data-video-label="${esc(pr.name)} — ${esc(i18n.modalCaption)}">
      <span class="iphone-notch" aria-hidden="true"></span>
      <span class="iphone-screen">
        <video class="iphone-video" loop muted playsinline preload="metadata" poster="${esc(pr.poster)}" aria-hidden="true" width="194" height="426" src="${esc(pr.video)}"></video>
      </span>
      <span class="iphone-home-bar" aria-hidden="true"></span>
    </button>
    <figcaption class="project-caption">${esc(caption)}</figcaption>
  </figure>
  <div class="project-info">
    <p class="project-tag">${esc(tag)}${trainingBadge}</p>
    <h3 class="project-name">${esc(pr.name)}</h3>
    <p class="project-desc">${esc(desc)}</p>
    <div class="tech-tags">${tech}</div>
    <div class="project-links">${links}</div>
  </div>
</article>`;
}

// ---------- modale vidéo AA (role=dialog, aria-modal, focus trap, ESC, retour focus, ✕ labellisé) ----------
export function videoModal({ i18n }) {
  // Fermé = attribut `hidden` (retiré du rendu ET de l'arbre a11y) plutôt qu'aria-hidden :
  // évite le conflit "aria-hidden sur ancêtre d'un élément focusable" (close + video controls).
  // À l'ouverture, le JS retire `hidden`. `controls` ajouté par le JS uniquement quand ouvert.
  return `<div class="video-modal" id="video-modal" role="dialog" aria-modal="true" aria-labelledby="video-modal-label" tabindex="-1" hidden>
  <div class="video-modal-dialog">
    <button type="button" class="video-modal-close" aria-label="${esc(i18n.modalClose)}">&#x2715;</button>
    <div class="video-modal-frame">
      <div class="iphone-notch" aria-hidden="true"></div>
      <div class="iphone-screen">
        <!-- Démos = screencasts muets, sans piste audio : aucun sous-titre requis (WCAG 1.2.2
             ne s'applique pas à un média sans audio). Légende visible (caption) en dessous. -->
        <video class="video-modal-video" loop muted playsinline preload="metadata" width="314" height="678"></video>
      </div>
      <div class="iphone-home-bar" aria-hidden="true"></div>
    </div>
    <p class="video-modal-caption" id="video-modal-label">${esc(i18n.modalCaption)}</p>
  </div>
</div>`;
}

// ---------- modale Calendly AA (réutilisée sur surfaces qui l'offrent) ----------
// role=dialog + aria-modal + focus trap + ESC + retour focus + ✕ labellisé + lazy-load.
export function calendlySection({ site, lang, sectionLabel, sectionTitle }) {
  const c = site[lang].calendly;
  return `<div class="calendly-block">
  <button type="button" class="btn-ghost calendly-load" id="calendly-load" data-calendly-url="${esc(c.url)}" data-widget-aria="${esc(c.widgetAria)}">${esc(c.load)}</button>
  <p class="calendly-notice" id="calendly-wrapper">${esc(c.notice)}</p>
</div>`;
}

// ---------- script client minimal (switcher mémorisation SANS auto-redirect + Calendly lazy + skip-link focus) ----------
export const CLIENT_JS = `(function(){
  "use strict";
  // Mémorisation du choix de langue (clé prim.lang) — AUCUN auto-redirect (piège Googlebot).
  // On ne fait que persister le dernier clic, jamais rediriger.
  try {
    var path = location.pathname;
    var isEn = path === "/en/" || path.indexOf("/en/") === 0 || path === "/en";
    document.querySelectorAll(".lang-switch a.lang-opt").forEach(function(a){
      a.addEventListener("click", function(){
        try { localStorage.setItem("prim.lang", a.getAttribute("hreflang")); } catch(e){}
      });
    });
    // Reflète la langue courante de la page (la page sert déjà le bon contenu).
    try { localStorage.setItem("prim.lang", isEn ? "en" : "fr"); } catch(e){}
  } catch(e){}

  // Calendly click-to-load (RGPD : aucun cookie avant clic).
  var btn = document.getElementById("calendly-load");
  if (btn) {
    btn.addEventListener("click", function(){
      var url = btn.getAttribute("data-calendly-url");
      var aria = btn.getAttribute("data-widget-aria") || "Calendly";
      var wrapper = document.getElementById("calendly-wrapper");
      var widget = document.createElement("div");
      widget.className = "calendly-inline-widget";
      widget.setAttribute("data-url", url);
      widget.setAttribute("role", "region");
      widget.setAttribute("aria-label", aria);
      widget.style.minWidth = "320px";
      widget.style.height = "700px";
      if (wrapper && wrapper.parentNode) wrapper.parentNode.insertBefore(widget, wrapper);
      var css = document.createElement("link");
      css.rel = "stylesheet"; css.href = "https://assets.calendly.com/assets/external/widget.css";
      document.head.appendChild(css);
      var sc = document.createElement("script");
      sc.src = "https://assets.calendly.com/assets/external/widget.js"; sc.async = true;
      document.head.appendChild(sc);
      btn.hidden = true; if (wrapper) wrapper.hidden = true;
    }, { once: true });
  }

  // Modale vidéo AA : ouverture au clic sur un iphone-frame, focus trap, ESC, retour focus.
  var modal = document.getElementById("video-modal");
  if (modal) {
    var modalVideo = modal.querySelector(".video-modal-video");
    var modalCaption = modal.querySelector("#video-modal-label");
    var modalClose = modal.querySelector(".video-modal-close");
    var lastTrigger = null;
    var rm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");
    function reduced(){ return !!(rm && rm.matches); }

    function openModal(trigger){
      var src = trigger.getAttribute("data-video-src");
      if (!src) return;
      lastTrigger = trigger;
      modalCaption.textContent = trigger.getAttribute("data-video-label") || modalCaption.textContent;
      var poster = trigger.getAttribute("data-video-poster");
      if (poster) modalVideo.setAttribute("poster", poster);
      if (modalVideo.getAttribute("src") !== src) modalVideo.setAttribute("src", src);
      modalVideo.controls = true; // WCAG 2.2.2 : contrôles disponibles quand la vidéo est visible.
      modal.hidden = false;
      document.body.classList.add("modal-open");
      if (!reduced()) { var p = modalVideo.play(); if (p && p.catch) p.catch(function(){}); }
      window.requestAnimationFrame(function(){ modalClose.focus(); });
    }
    function closeModal(){
      if (modal.hidden) return;
      try { modalVideo.pause(); } catch(e){}
      modalVideo.controls = false;
      modal.hidden = true;
      document.body.classList.remove("modal-open");
      if (lastTrigger && lastTrigger.focus) lastTrigger.focus();
      lastTrigger = null;
    }
    document.querySelectorAll(".iphone-frame[data-video-src]").forEach(function(b){
      b.addEventListener("click", function(e){ e.preventDefault(); openModal(b); });
    });

    // Lecture continue des vignettes pilotée par JS (pas l'attribut autoplay, banni par
    // WCAG 2.2.2 / html-validate) : lecture quand visible, pause hors écran (perf/batterie).
    // Respecte prefers-reduced-motion (WCAG 2.3.3 / R9) : aucune animation auto si réduit.
    var tiles = document.querySelectorAll(".iphone-frame .iphone-video");
    if (tiles.length) {
      function playTile(v){ if (reduced()) return; var p = v.play(); if (p && p.catch) p.catch(function(){}); }
      if ("IntersectionObserver" in window) {
        var io = new IntersectionObserver(function(entries){
          entries.forEach(function(en){
            if (en.isIntersecting) playTile(en.target);
            else { try { en.target.pause(); } catch(e){} }
          });
        }, { threshold: 0.25 });
        tiles.forEach(function(v){ io.observe(v); });
      } else {
        tiles.forEach(playTile);
      }
      // Coupe l'animation si l'utilisateur active "réduire les animations" en cours de session.
      if (rm && rm.addEventListener) {
        rm.addEventListener("change", function(){
          tiles.forEach(function(v){
            if (reduced()) { try { v.pause(); } catch(e){} }
            else playTile(v);
          });
        });
      }
    }
    modalClose.addEventListener("click", closeModal);
    modal.addEventListener("click", function(e){ if (e.target === modal) closeModal(); });
    document.addEventListener("keydown", function(e){
      if (modal.hidden) return;
      if (e.key === "Escape") { e.preventDefault(); closeModal(); return; }
      if (e.key === "Tab") {
        var f = [modalClose]; if (modalVideo.controls) f.push(modalVideo);
        var first = f[0], last = f[f.length-1], a = document.activeElement;
        if (e.shiftKey) { if (a === first || !modal.contains(a)) { e.preventDefault(); last.focus(); } }
        else { if (a === last || !modal.contains(a)) { e.preventDefault(); first.focus(); } }
      }
    });
  }
})();`;

// ---------- layout ----------
export function layout({ site, config, lang, route, pageMeta, jsonldType, app, bodyHtml, extraHtml = "" }) {
  const s = site[lang];
  return `<!DOCTYPE html>
<html lang="${esc(lang)}" dir="${esc(s.dir)}">
<head>
${head({ site, config, lang, route, pageMeta, jsonldType, app })}
</head>
<body>
<a href="#main" class="skip-link">${esc(s.skipLink)}</a>
${header({ site, lang, route })}
<main id="main" tabindex="-1">
${bodyHtml}
</main>
${footer({ site, lang })}
${extraHtml}
<script>${CLIENT_JS}</script>
</body>
</html>
`;
}
