// scripts/lib/render-pages.mjs — Corps <main> par type de page. Ordre de titres h1→h2→h3 réel.
// La numérotation « 01 — » est décorative (span aria-hidden), jamais un niveau de titre.

import { esc, raw, appCard, appCtaButton, calendlySection, projectCard } from "./templates.mjs";
import { appHasVisibleCard } from "./validate.mjs";

// Libellé de section avec numéro décoratif (aria-hidden) + texte réel lisible par AT.
function sectionLabel(num, text) {
  return `<p class="section-label"><span class="deco-num" aria-hidden="true">${num} — </span>${esc(text)}</p>`;
}

// Numérotation à 2 chiffres, déterministe (« 01 », « 02 »…).
const pad2 = (n) => String(n).padStart(2, "0");

// ---------- HOME ----------
export function renderHome({ page, site, apps, lang }) {
  const p = page[lang];
  const cta = site[lang].cta;
  const flagship = apps.find((a) => a.id === p.hero.ctaPrimary.appId);

  // Hero studio — zéro mention CDI.
  const primaryCta = flagship
    ? appCtaButton({ app: flagship, site, lang, primary: true })
    : "";
  const secLabel = lang === "fr" ? p.hero.ctaSecondary.labelFr : p.hero.ctaSecondary.labelEn;
  const hero = `<section class="hero" aria-labelledby="home-h1">
  <p class="hero-label">${esc(p.hero.label)}</p>
  <h1 id="home-h1">${raw(p.hero.title)}</h1>
  <p class="hero-desc">${esc(p.hero.desc)}</p>
  <div class="hero-cta">
    ${primaryCta}
    <a class="btn-ghost" href="${esc(p.hero.ctaSecondary.href)}">${esc(secLabel)}</a>
  </div>
</section>`;

  // Section flagship FicheChef — preuve produit (screenshots réels ou emplacement honnête).
  let flagshipSection = "";
  if (flagship) {
    const shots = Array.isArray(flagship.screenshots) ? flagship.screenshots : [];
    const proof =
      shots.length > 0
        ? `<div class="shot-grid">${shots
            .map(
              (s) =>
                `<img src="${esc(s.src)}" alt="${esc(s.alt[lang])}" loading="lazy" width="280" height="606">`
            )
            .join("")}</div>`
        : `<p class="draft-line">${lang === "fr" ? "Captures d'écran à venir — déposées au lancement." : "Screenshots coming — added at launch."}</p>`;
    flagshipSection = `<section id="flagship" aria-labelledby="flagship-h2">
  ${sectionLabel("01", p.flagship.label)}
  <h2 class="section-title" id="flagship-h2">${esc(flagship.name)}</h2>
  <p class="section-subtitle">${esc(flagship.summary[lang])}</p>
  ${proof}
  <div class="hero-cta">
    <a class="btn-ghost" href="${lang === "fr" ? "/fichechef" : "/en/fichechef"}">${esc(cta.learnMore)} →</a>
  </div>
</section>`;
  }

  // Grille apps status-aware.
  const visible = apps.filter((a) => appHasVisibleCard(a));
  const hidden = apps.filter((a) => !appHasVisibleCard(a) && a.showOnHome);
  const cards = visible.map((a) => appCard({ app: a, site, lang })).join("\n  ");
  const draftLine =
    hidden.length > 0
      ? `<p class="draft-line"><strong>${esc(p.apps.draftMoreLabel)} :</strong> ${esc(
          hidden.map((a) => a.name).join(", ")
        )}.</p>`
      : "";
  const appsSection = `<section id="apps" aria-labelledby="apps-h2">
  ${sectionLabel("02", p.apps.label)}
  <h2 class="section-title" id="apps-h2">${esc(p.apps.title)}</h2>
  <p class="section-subtitle">${esc(p.apps.subtitle)}</p>
  <div class="card-grid cols-3">
  ${cards}
  </div>
  ${draftLine}
</section>`;

  // Méthode (reframe stack en argument produit).
  const methodCards = p.methode.cards
    .map((c) => `<div class="feat-card"><h3>${esc(c.title)}</h3><p>${esc(c.desc)}</p></div>`)
    .join("\n    ");
  const methodSection = `<section id="methode" aria-labelledby="methode-h2">
  ${sectionLabel("03", p.methode.label)}
  <h2 class="section-title" id="methode-h2">${esc(p.methode.title)}</h2>
  <p class="section-subtitle">${esc(p.methode.subtitle)}</p>
  <div class="card-grid cols-4">
    ${methodCards}
  </div>
</section>`;

  // Teaser fondateur.
  const founderSection = `<section id="fondateur" aria-labelledby="fondateur-h2">
  ${sectionLabel("04", p.founder.label)}
  <h2 class="section-title" id="fondateur-h2">${esc(p.founder.title)}</h2>
  <p class="section-subtitle">${esc(p.founder.body)}</p>
  <a class="btn-ghost" href="${esc(p.founder.linkHref)}" aria-label="${esc(p.founder.linkLabel)}">${lang === "fr" ? "À propos du studio" : "About the studio"} →</a>
</section>`;

  // Contact B2B/presse primaire ; Calendly secondaire.
  const contactSection = `<section id="contact" class="contact-section" aria-labelledby="contact-h2">
  ${sectionLabel("05", p.contact.label)}
  <h2 class="section-title" id="contact-h2">${raw(p.contact.title)}</h2>
  <p class="contact-desc">${esc(p.contact.desc)}</p>
  <div class="contact-links">
    <a class="contact-link" href="mailto:${esc(p.contact.email)}" aria-label="${esc(p.contact.emailAria)}">✉ ${esc(cta.contactEmail)}</a>
    <a class="contact-link" href="${esc(site[lang].social.github)}" rel="noopener" aria-label="${lang === "fr" ? "GitHub — profil de Prim" : "GitHub — Prim's profile"}">GitHub ↗</a>
  </div>
  ${calendlySection({ site, lang })}
</section>`;

  return [hero, flagshipSection, appsSection, methodSection, founderSection, contactSection].join("\n");
}

// ---------- APP (page produit FicheChef, gabarit réutilisable) ----------
export function renderApp({ page, site, app, lang }) {
  const p = page[lang];
  const cta = site[lang].cta;

  const primaryCta = appCtaButton({ app, site, lang, primary: true });
  const shots = Array.isArray(app.screenshots) ? app.screenshots : [];
  const proof =
    shots.length > 0
      ? `<div class="shot-grid">${shots
          .map((s) => `<img src="${esc(s.src)}" alt="${esc(s.alt[lang])}" loading="lazy" width="280" height="606">`)
          .join("")}</div>`
      : `<p class="draft-line">${lang === "fr" ? "Captures d'écran à venir — emplacement réservé." : "Screenshots coming — placeholder reserved."}</p>`;

  const benefits = p.benefits.items
    .map((b) => `<div class="feat-card"><h3>${esc(b.title)}</h3><p>${esc(b.desc)}</p></div>`)
    .join("\n    ");

  const diffLabel = lang === "fr" ? "Différenciateurs" : "Differentiators";
  const diffs = (app.differentiators[lang] || [])
    .map((d) => `<li>${esc(d)}</li>`)
    .join("");

  const privacyHref = app.links?.privacy?.[lang] || (lang === "fr" ? "/fichechef/privacy" : "/en/fichechef/privacy");
  const supportHref = app.links?.support?.[lang] || (lang === "fr" ? "/fichechef/support" : "/en/fichechef/support");

  return `<section class="hero product-hero" aria-labelledby="app-h1">
  <p class="hero-label">${esc(p.hero.label)}</p>
  <h1 id="app-h1">${esc(p.hero.h1)}</h1>
  <p class="product-problem">${esc(app.tagline[lang])}</p>
  <p class="hero-desc">${esc(p.hero.problem)}</p>
  <div class="hero-cta">${primaryCta}</div>
</section>
<section aria-labelledby="proof-h2">
  ${sectionLabel("01", lang === "fr" ? "Aperçu" : "Preview")}
  <h2 class="section-title" id="proof-h2">${lang === "fr" ? "L'app en images" : "The app in pictures"}</h2>
  ${proof}
</section>
<section aria-labelledby="benefits-h2">
  ${sectionLabel("02", p.benefits.label)}
  <h2 class="section-title" id="benefits-h2">${esc(p.benefits.title)}</h2>
  <div class="card-grid cols-2">
    ${benefits}
  </div>
  ${diffs ? `<h3 class="sr-only">${esc(diffLabel)}</h3><ul class="diff-list">${diffs}</ul>` : ""}
</section>
<section aria-labelledby="res-h2">
  ${sectionLabel("03", p.appLinks.label)}
  <h2 class="section-title" id="res-h2">${lang === "fr" ? "Ressources FicheChef" : "FicheChef resources"}</h2>
  <div class="contact-links contact-links-left">
    <a class="contact-link" href="${esc(privacyHref)}">${esc(p.appLinks.privacyLabel)}</a>
    <a class="contact-link" href="${esc(supportHref)}">${esc(p.appLinks.supportLabel)}</a>
  </div>
</section>`;
}

// ---------- ABOUT (studio + fondateur + démos portfolio + bloc Collaborer CDI/missions) ----------
export function renderAbout({ page, site, lang, projectsDoc }) {
  const p = page[lang];
  const cta = site[lang].cta;
  const c = p.collaborate;

  const studioBody = p.studio.body.map((x) => `<p>${esc(x)}</p>`).join("\n  ");
  const founderBody = p.founder.body.map((x) => `<p>${esc(x)}</p>`).join("\n  ");

  // Section démos unique (T1 — fusion) entre fondateur et Collaborer. Tous les projets
  // dans « Applications livrées » ; les projets de formation gardent leur badge honnête.
  let n = 2; // studio=01, fondateur=02.
  let projectSections = "";
  if (projectsDoc) {
    const pi = projectsDoc.i18n[lang];
    const items = projectsDoc.projects; // group unique : plus de filtrage production/lab.
    if (items.length) {
      n += 1;
      const cards = items.map((pr) => projectCard({ project: pr, i18n: pi, lang })).join("\n    ");
      projectSections = `\n<section aria-labelledby="production-h2">
  ${sectionLabel(pad2(n), pi.productionLabel)}
  <h2 class="section-title" id="production-h2">${esc(pi.productionLabel)}</h2>
  <p class="section-subtitle">${esc(pi.productionSubtitle)}</p>
  <div class="projects-grid">
    ${cards}
  </div>
</section>`;
    }
  }
  n += 1;
  const collabNum = pad2(n);

  return `<section class="hero" aria-labelledby="about-h1">
  <p class="hero-label">${esc(p.hero.label)}</p>
  <h1 id="about-h1">${raw(p.hero.title)}</h1>
  <p class="hero-desc">${esc(p.hero.desc)}</p>
</section>
<section aria-labelledby="studio-h2">
  ${sectionLabel("01", p.studio.label)}
  <h2 class="section-title" id="studio-h2">${esc(p.studio.title)}</h2>
  <div class="prose">${studioBody}</div>
</section>
<section aria-labelledby="founder-h2">
  ${sectionLabel("02", p.founder.label)}
  <h2 class="section-title" id="founder-h2">${esc(p.founder.title)}</h2>
  <div class="prose">${founderBody}</div>
</section>${projectSections}
<section aria-labelledby="collab-h2">
  ${sectionLabel(collabNum, c.label)}
  <div class="collaborate">
    <h2 class="section-title collab-title" id="collab-h2">${esc(c.title)}</h2>
    <p class="availability">${esc(c.availability)}</p>
    <p class="pitch">${esc(c.pitch)}</p>
    <div class="collaborate-cta">
      <a class="btn-primary" href="mailto:${esc(c.ctaPrimaryEmail)}" aria-label="${esc(c.ctaPrimaryEmailAria)}">✉ ${esc(cta.contactEmail)}</a>
      <a class="btn-primary" href="${esc(c.ctaCvHref)}" target="_blank" rel="noopener" aria-label="${esc(c.ctaCvAria)}">${esc(cta.viewCv)} ↗</a>
    </div>
    <div class="calendly-block">
      <p class="calendly-prompt">${lang === "fr" ? "Ou réservez un créneau :" : "Or book a slot:"}</p>
      ${calendlySection({ site, lang })}
    </div>
  </div>
</section>`;
}

// ---------- LEGAL / SUPPORT (prose bilingue migrée) ----------
export function renderLegal({ page, site, lang }) {
  const p = page[lang];
  const intro = p.intro ? `<p class="intro-note">${raw(p.intro)}</p>` : "";
  const updated = p.updated ? `<p class="updated">${esc(p.updated)}</p>` : "";

  const sections = (p.sections || [])
    .map((sec) => {
      const body = (sec.body || []).map((b) => `<p>${raw(b)}</p>`).join("\n    ");
      return `<h2>${esc(sec.h2)}</h2>\n    ${body}`;
    })
    .join("\n    ");

  let contactCard = "";
  if (p.contactCard) {
    const subj = p.contactCard.mailtoSubject
      ? `?subject=${encodeURIComponent(p.contactCard.mailtoSubject)}`
      : "";
    const cbody = p.contactCard.body ? `<p>${raw(p.contactCard.body)}</p>` : "";
    contactCard = `<div class="contact-card">
    <p><strong>${lang === "fr" ? "Contact" : "Contact"} :</strong> <a href="mailto:${esc(p.contactCard.email)}${subj}">${esc(p.contactCard.email)}</a></p>
    ${cbody}
  </div>`;
  }

  const blocks = [`<h1 id="legal-h1">${esc(p.h1)}</h1>`, updated, intro, contactCard, sections]
    .filter((b) => b && b.trim().length > 0)
    .join("\n  ");
  // Wrapper <section class="legal"> : hérite du padding (compense le header fixe + marges
  // horizontales) que les pages home/about obtiennent via leur <section class="hero">.
  return `<section class="legal" aria-labelledby="legal-h1">\n<article class="prose">\n  ${blocks}\n</article>\n</section>`;
}
