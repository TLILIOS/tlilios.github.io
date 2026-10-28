// scripts/lib/jsonld.mjs — Générateurs JSON-LD status-aware, dérivés des données.
// Jamais écrit à la main par page. Aucune donnée fabriquée :
//  - SoftwareApplication SANS `offers` ni `aggregateRating` tant que l'app n'est pas publiée.
//  - `screenshot` seulement si des captures réelles existent.

const escapeJson = (s) => String(s); // JSON.stringify gère l'échappement ; helper sémantique.

export function organizationNode(SITE_URL) {
  return {
    "@type": "Organization",
    "@id": `${SITE_URL}/#prim`,
    name: "Prim",
    // Pas de legalName : les mentions légales ne nomment que l'éditeur (TLILI HAMDI, EI), pas Prim.
    alternateName: ["Prim Studio"],
    description:
      "Studio indépendant d'applications iOS natives premium — pour les pros et la conformité française.",
    url: `${SITE_URL}/`,
    // Tuile 512 px (option A validée), lisible sur fond blanc ; générée par scripts/brand/generate.py.
    logo: { "@type": "ImageObject", url: `${SITE_URL}/prim-logo-512.png`, width: 512, height: 512 },
    founder: { "@id": `${SITE_URL}/#person` },
    address: { "@type": "PostalAddress", addressLocality: "Paris", addressCountry: "FR" },
  };
}

export function personNode(SITE_URL) {
  return {
    "@type": "Person",
    "@id": `${SITE_URL}/#person`,
    name: "TLILI HAMDI",
    givenName: "Hamdi",
    familyName: "Tlili",
    jobTitle: "Senior iOS Developer",
    description:
      "Développeur iOS senior (SwiftUI, Swift 6, MVVM + Clean Architecture), fondateur du studio Prim. Ouvert à un CDI senior ou des missions.",
    url: `${SITE_URL}/a-propos`,
    image: `${SITE_URL}/og-image.png`,
    email: "mailto:hamdi.tlili@primapp.dev",
    address: { "@type": "PostalAddress", addressLocality: "Paris", addressCountry: "FR" },
    worksFor: { "@id": `${SITE_URL}/#prim` },
    sameAs: [
      "https://github.com/TLILIOS",
      "https://www.linkedin.com/in/hamdi-tlili-b83122153/",
      "https://x.com/TliliOS",
    ],
    knowsAbout: [
      "iOS Development",
      "SwiftUI",
      "Swift 6",
      "MVVM",
      "Clean Architecture",
      "SwiftData",
      "Accessibility",
      "WCAG",
    ],
    knowsLanguage: ["fr", "en"],
    seeks: {
      "@type": "Demand",
      name: "Poste de Senior iOS Developer en CDI",
      itemOffered: {
        "@type": "JobPosting",
        title: "Senior iOS Developer",
        employmentType: "FULL_TIME",
      },
    },
  };
}

export function websiteNode(SITE_URL, lang) {
  return {
    "@type": "WebSite",
    "@id": `${SITE_URL}/#website`,
    url: `${SITE_URL}/`,
    name: "Prim",
    alternateName: ["Prim Studio"],
    description:
      lang === "en"
        ? "Prim, an independent studio building premium native iOS apps for professionals and French compliance."
        : "Prim, studio indépendant d'applications iOS natives premium pour les pros et la conformité française.",
    inLanguage: ["fr-FR", "en-US"],
    publisher: { "@id": `${SITE_URL}/#prim` },
  };
}

// Page produit : SoftwareApplication status-aware.
// Émet `offers` UNIQUEMENT si l'app est publiée (appStoreUrl non null) — sinon pas d'offers.
// `screenshot` uniquement si captures réelles. Jamais d'aggregateRating fabriqué.
export function softwareApplicationNode(SITE_URL, app, lang) {
  const node = {
    "@type": "SoftwareApplication",
    "@id": `${SITE_URL}/#app-${app.id}`,
    name: app.name,
    applicationCategory: app.applicationCategory || "BusinessApplication",
    operatingSystem: app.operatingSystem || "iOS",
    description: (app.summary && app.summary[lang]) || (app.tagline && app.tagline[lang]) || app.name,
    author: { "@id": `${SITE_URL}/#prim` },
    publisher: { "@id": `${SITE_URL}/#prim` },
  };

  const shots = Array.isArray(app.screenshots) ? app.screenshots : [];
  if (shots.length > 0) {
    node.screenshot = shots.map((s) => `${SITE_URL}${s.src}`);
  }

  // Publié = appStoreUrl renseignée. Tant que non publié : pas d'offers, pas de rating.
  const isPublished = !!app.appStoreUrl && app.status === "available";
  if (isPublished) {
    node.downloadUrl = app.appStoreUrl;
    // offers uniquement à la publication, prix réel (0 si gratuit) à renseigner par l'humain.
    if (typeof app.priceEUR === "number") {
      node.offers = {
        "@type": "Offer",
        price: String(app.priceEUR),
        priceCurrency: "EUR",
      };
    }
  }
  return node;
}

// Construit le bloc @graph complet selon le type de page.
export function buildGraph({ type, SITE_URL, lang, app }) {
  let nodes;
  switch (type) {
    case "home":
      nodes = [organizationNode(SITE_URL), websiteNode(SITE_URL, lang)];
      break;
    case "app":
      nodes = [softwareApplicationNode(SITE_URL, app, lang), organizationNode(SITE_URL)];
      break;
    case "about":
      nodes = [personNode(SITE_URL), organizationNode(SITE_URL)];
      break;
    default:
      nodes = [organizationNode(SITE_URL)];
  }
  return { "@context": "https://schema.org", "@graph": nodes };
}

export function renderJsonLd(graph) {
  // Indentation stable (déterminisme du build), pas de timestamp.
  return `<script type="application/ld+json">\n${JSON.stringify(graph, null, 2)}\n</script>`;
}
