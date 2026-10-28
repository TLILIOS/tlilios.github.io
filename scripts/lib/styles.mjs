// scripts/lib/styles.mjs — Feuille de style unique, écrite en /assets/site.css par le build.
// Tokens couleur vérifiés contre --bg-deep #08090c (WCAG 2.2 AA, ADR-0003).
// Contrastes (vérifiés) : --text-primary #eceef4 ~16:1 ; --text-secondary #a3a8bd ~8:1 ;
// --text-muted #868ba0 ~5,07:1 (>=4.5) ; --accent #b8c8ff ~10:1.

export const SITE_CSS = `*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg-deep:#08090c;--bg-card:#161922;--bg-elevated:#1c2030;
  /* T4 dark-only : surface de carte distincte (#161922 vs fond #08090c) + hairline plus lisible.
     bordure 1px portée de .08 à .14 alpha pour détacher la carte du fond très sombre. */
  --border:rgba(255,255,255,.08);--border-card:rgba(255,255,255,.14);
  --text-primary:#eceef4;--text-secondary:#a3a8bd;--text-muted:#868ba0;
  --accent:#b8c8ff;--accent-strong:#d0dcff;--accent-glow:rgba(160,180,245,.12);
  --gradient-hero:linear-gradient(165deg,#0d0f16 0%,#111422 40%,#0f1119 100%);
  --serif:Georgia,'Times New Roman',serif;
  --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
  --mono:'SF Mono','Cascadia Code','Consolas',monospace;
}
html{scroll-behavior:smooth}
body{background:var(--bg-deep);color:var(--text-primary);font-family:var(--sans);font-weight:300;line-height:1.7;overflow-x:hidden;-webkit-font-smoothing:antialiased}
::selection{background:var(--accent);color:var(--bg-deep)}
a{color:var(--accent)}
img,video{max-width:100%}

.skip-link{position:absolute;top:-100px;left:1rem;background:var(--accent);color:var(--bg-deep);padding:.6rem 1rem;border-radius:6px;font-size:.85rem;font-weight:500;text-decoration:none;z-index:1000;transition:top .2s}
.skip-link:focus{top:1rem}
main:focus{outline:none}

a:focus-visible,button:focus-visible,.lang-opt:focus-visible,.btn-primary:focus-visible,.btn-ghost:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:4px}

/* header */
header nav{position:fixed;top:0;left:0;right:0;z-index:100;padding:1.4rem 3rem;display:flex;justify-content:space-between;align-items:center;background:rgba(8,9,12,.72);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);border-bottom:1px solid var(--border)}
.nav-logo{font-family:var(--serif);font-size:1.4rem;color:var(--text-primary);text-decoration:none}
/* PRIM (SVG intégré) à la hauteur de capitale de Georgia : même boîte de ligne que l'ancien texte, CLS nul. */
.wordmark{height:.6929em;width:auto;vertical-align:baseline}
.nav-right{display:flex;align-items:center;gap:2rem}
.nav-links{display:flex;gap:2.2rem;list-style:none}
.nav-links a{color:var(--text-secondary);text-decoration:none;font-size:.82rem;font-weight:400;letter-spacing:.08em;text-transform:uppercase;transition:color .3s}
.nav-links a:hover{color:var(--text-primary)}

/* lang switch — texte FR/EN, pas de drapeau */
.lang-switch{display:inline-flex;align-items:center;gap:.15rem;background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:999px;padding:.2rem .35rem;font-family:var(--mono);font-size:.72rem;letter-spacing:.1em}
.lang-switch .lang-opt{padding:.3rem .6rem;border-radius:999px;color:var(--text-secondary);text-decoration:none;transition:background .3s,color .3s}
.lang-switch a.lang-opt:hover{color:var(--text-primary)}
.lang-switch .lang-opt[aria-current="page"]{background:var(--accent);color:var(--bg-deep);font-weight:600}
.lang-sep{color:var(--text-muted)}

.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}

/* hero */
/* background-color solide explicite EN PLUS du gradient : permet à axe de calculer
   le contraste réel (sans fallback solide, un background-image gradient laisse axe
   en "incomplete" → faux positif pa11y). Le ton solide reste un fond sombre conforme. */
.hero{min-height:88vh;display:flex;flex-direction:column;justify-content:center;padding:9rem 3rem 4rem;background-color:#0e1019;background-image:var(--gradient-hero);position:relative;overflow:hidden}
.hero::after{content:"";position:absolute;bottom:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,var(--border),transparent)}
.hero-label{font-family:var(--mono);font-size:.72rem;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);margin-bottom:1.8rem}
.hero h1{font-family:var(--serif);font-size:clamp(2.6rem,6.5vw,5.8rem);font-weight:400;line-height:1.06;letter-spacing:-.02em;margin-bottom:1.8rem}
.hero h1 em{font-style:italic;color:var(--accent)}
.hero-desc{max-width:560px;font-size:1.05rem;color:var(--text-secondary);line-height:1.8;margin-bottom:2.6rem}
.hero-cta{display:flex;gap:1.4rem;align-items:center;flex-wrap:wrap}

/* T3 : variantes unifiées. Padding/rayon/cible tactile (>=44px) cohérents.
   États hover/focus-visible/active/disabled homogènes. .btn-primary = CTA plein,
   .btn-ghost = secondaire bordé (plus seulement un soulignement). */
.btn-primary,.btn-ghost{display:inline-flex;align-items:center;justify-content:center;gap:.5rem;min-height:44px;padding:.8rem 1.8rem;font-size:.85rem;font-weight:500;font-family:var(--sans);text-decoration:none;border-radius:8px;cursor:pointer;line-height:1;transition:background .25s,color .25s,border-color .25s,transform .15s,box-shadow .25s}
.btn-primary,.btn-ghost{will-change:transform}
.btn-primary{background:var(--accent);color:var(--bg-deep);border:1px solid var(--accent)}
.btn-primary:hover{background:var(--accent-strong);border-color:var(--accent-strong);box-shadow:0 8px 32px rgba(184,200,255,.28);transform:translateY(-1px)}
.btn-primary:active{transform:translateY(0);box-shadow:0 3px 12px rgba(184,200,255,.22)}
.btn-ghost{background:rgba(255,255,255,.03);color:var(--text-primary);border:1px solid var(--border-card)}
.btn-ghost:hover{color:var(--text-primary);border-color:var(--accent);background:var(--accent-glow)}
.btn-ghost:active{transform:translateY(0);background:rgba(160,180,245,.16)}
/* disabled cohérent sur les deux variantes (jamais cliquable, non focusable via aria-disabled). */
.is-disabled,.btn-primary.is-disabled,.btn-ghost.is-disabled{opacity:.55;cursor:not-allowed;transform:none;box-shadow:none;pointer-events:none;background:var(--bg-elevated);color:var(--text-muted);border-color:var(--border)}

/* sections */
section{padding:6.5rem 3rem;position:relative;scroll-margin-top:5rem}
section::after{content:"";position:absolute;bottom:0;left:3rem;right:3rem;height:1px;background:var(--border)}
section:last-of-type::after{display:none}
.section-label{font-family:var(--mono);font-size:.7rem;letter-spacing:.2em;text-transform:uppercase;color:var(--text-muted);margin-bottom:1rem}
.section-label .deco-num{color:var(--accent);opacity:.6}
.section-title{font-family:var(--serif);font-size:clamp(2rem,4vw,3.1rem);font-weight:400;margin-bottom:1rem;line-height:1.2}
.section-title em{font-style:italic;color:var(--accent)}
.section-subtitle{color:var(--text-secondary);font-size:.95rem;margin-bottom:2.6rem;max-width:640px}

/* méthode / cards génériques */
.card-grid{display:grid;gap:1.4rem}
.card-grid.cols-4{grid-template-columns:repeat(4,1fr)}
.card-grid.cols-3{grid-template-columns:repeat(3,1fr)}
.card-grid.cols-2{grid-template-columns:repeat(2,1fr)}
.feat-card{background:var(--bg-card);border:1px solid var(--border-card);border-radius:14px;padding:1.8rem;transition:border-color .3s,transform .3s}
.feat-card:hover{border-color:rgba(160,180,245,.18);transform:translateY(-2px)}
.feat-card h3{font-size:1rem;font-weight:500;margin-bottom:.7rem;color:var(--text-primary)}
.feat-card p{font-size:.86rem;color:var(--text-secondary);line-height:1.65}

/* app cards (grille home) */
.app-card{background:var(--bg-card);border:1px solid var(--border-card);border-radius:14px;padding:1.6rem 1.7rem;display:flex;flex-direction:column;gap:.6rem;transition:border-color .3s,transform .3s}
.app-card:hover{border-color:rgba(160,180,245,.18);transform:translateY(-2px)}
.app-card-head{display:flex;align-items:center;gap:.6rem;flex-wrap:wrap}
.app-card-name{font-family:var(--serif);font-size:1.4rem}
.app-card-category{font-family:var(--mono);font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;color:var(--text-muted)}
.app-card-tagline{font-size:.9rem;color:var(--text-secondary);line-height:1.6}
.app-card-link{font-size:.82rem;color:var(--accent);text-decoration:none;margin-top:.3rem}
.app-card-link:hover{text-decoration:underline}
.app-card-flagship{font-family:var(--mono);font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);border:1px solid rgba(184,200,255,.35);border-radius:999px;padding:.18rem .55rem}
.status-badge{font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;border-radius:999px;padding:.2rem .6rem;border:1px solid var(--border);color:var(--text-secondary)}
.status-available{color:#7be0a3;border-color:rgba(123,224,163,.4)}
.status-coming-soon{color:var(--accent);border-color:rgba(184,200,255,.4)}
.draft-line{font-size:.86rem;color:var(--text-muted);margin-top:1.4rem}
.draft-line strong{color:var(--text-secondary);font-weight:500}

.shot-grid{display:flex;gap:1.4rem;flex-wrap:wrap;margin:1.6rem 0}
.shot-grid img{border-radius:24px;border:1px solid var(--border)}
.diff-list{display:flex;gap:.6rem;flex-wrap:wrap;list-style:none;margin-top:1.6rem}
.diff-list li{font-family:var(--mono);font-size:.72rem;letter-spacing:.06em;color:var(--text-secondary);background:rgba(160,180,245,.07);border:1px solid rgba(160,180,245,.12);border-radius:999px;padding:.4rem .9rem}

/* prose (pages légales / produit) */
/* page légale : 1re section sans hero → top padding pour dégager le header fixe + prose centrée. */
.legal{padding-top:9rem}
.prose{max-width:760px;margin-inline:auto}
.prose h1{font-family:var(--serif);font-size:clamp(2rem,4vw,2.8rem);font-weight:400;margin-bottom:1.2rem;line-height:1.15}
.prose h2{font-family:var(--serif);font-size:1.4rem;font-weight:400;margin:2.2rem 0 .8rem}
.prose h3{font-size:1.05rem;font-weight:500;margin:1.6rem 0 .6rem}
.prose p{color:var(--text-secondary);margin-bottom:1rem}
.prose strong{color:var(--text-primary);font-weight:500}
.prose a{color:var(--accent)}
.prose .updated{font-size:.82rem;color:var(--text-muted);margin-top:2rem}
.prose .intro-note{font-style:italic;color:var(--text-muted);font-size:.9rem}
.contact-card{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:1.4rem 1.6rem;margin:1.4rem 0}
.contact-card a{font-weight:500}

/* benefits / produit */
.product-hero{padding-top:9rem}
.product-problem{font-size:1.05rem;color:var(--text-secondary);max-width:620px;line-height:1.8;margin-bottom:2.2rem}

/* collaborate block (about) — section identifiée, délimitée */
/* Fond solide computable (#13151f ≈ teinte du gradient bleuté sur fond sombre) :
   garantit que le texte muted/secondary garde >=4.5:1 ET qu'axe calcule au lieu de rester incomplete. */
.collaborate{background-color:#13151f;background-image:linear-gradient(180deg,rgba(184,200,255,.05),rgba(184,200,255,.015));border:1px solid rgba(184,200,255,.25);border-radius:16px;padding:2.4rem;margin-top:2rem}
.collaborate .availability{font-family:var(--mono);font-size:.74rem;letter-spacing:.06em;color:var(--accent);margin:.8rem 0 1.4rem}
.collaborate .pitch{color:var(--text-secondary);margin-bottom:1.6rem;max-width:640px}
.collaborate .collab-title{margin-top:0}
.calendly-prompt{font-size:.85rem;color:var(--text-secondary);margin-bottom:.4rem}
.collaborate-cta{display:flex;gap:1.4rem;align-items:center;flex-wrap:wrap}

/* contact */
.contact-section{text-align:center}
.contact-section .section-title{font-size:clamp(2.2rem,5vw,3.6rem)}
.contact-desc{color:var(--text-secondary);max-width:480px;margin:0 auto 2.4rem}
.contact-links{display:flex;justify-content:center;gap:1.4rem;flex-wrap:wrap}
.contact-links-left{justify-content:flex-start}
.contact-link{display:inline-flex;align-items:center;gap:.5rem;color:var(--text-secondary);text-decoration:none;font-size:.88rem;padding:.7rem 1.4rem;border:1px solid var(--border);border-radius:8px;transition:color .3s,border-color .3s,background .3s}
.contact-link:hover{color:var(--text-primary);border-color:var(--accent);background:var(--accent-glow)}

/* calendly */
.calendly-block{margin-top:1.8rem}
.calendly-notice{font-size:.78rem;color:var(--text-muted);max-width:480px;margin-top:.8rem}
.calendly-inline-widget{min-width:320px;height:700px;border-radius:12px;overflow:hidden;border:1px solid var(--border);margin-top:1rem}

/* ---------- démos portfolio (project cards + iphone frame + modale vidéo) ---------- */
.projects-grid{display:grid;gap:2rem}
.project-card{background:var(--bg-card);border:1px solid var(--border-card);border-radius:16px;overflow:hidden;display:grid;grid-template-columns:1fr 1fr;transition:border-color .4s,transform .4s,box-shadow .4s}
.project-card:hover{border-color:rgba(184,200,255,.3);transform:translateY(-3px);box-shadow:0 24px 64px rgba(0,0,0,.4)}
.project-visual{margin:0;padding:3rem;display:flex;flex-direction:column;gap:1.2rem;align-items:center;justify-content:center;position:relative;overflow:hidden;min-height:420px;background:linear-gradient(135deg,#141826,#0f1119)}
.project-info{padding:2.6rem;display:flex;flex-direction:column;justify-content:center}
.project-tag{font-family:var(--mono);font-size:.68rem;letter-spacing:.15em;text-transform:uppercase;color:var(--accent);margin-bottom:1rem}
.project-badge{display:inline-block;font-family:var(--mono);font-size:.6rem;letter-spacing:.14em;text-transform:uppercase;color:var(--text-secondary);border:1px solid var(--border);border-radius:999px;padding:.28rem .7rem;margin-left:.6rem;vertical-align:middle}
.project-name{font-family:var(--serif);font-size:1.8rem;margin-bottom:.8rem;line-height:1.2}
.project-desc{color:var(--text-secondary);font-size:.92rem;margin-bottom:1.4rem;line-height:1.7}
.tech-tags{display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:1.2rem}
.tech-tag{font-family:var(--mono);font-size:.68rem;padding:.35rem .75rem;background:rgba(160,180,245,.07);border:1px solid rgba(160,180,245,.1);border-radius:20px;color:var(--text-secondary)}
.project-links{display:flex;gap:1rem;margin-top:auto;flex-wrap:wrap}
.project-link{font-size:.8rem;color:var(--accent);text-decoration:none;transition:opacity .3s}
.project-link:hover{opacity:.7;text-decoration:underline}
.project-caption{margin:0;font-family:var(--mono);font-size:.62rem;letter-spacing:.12em;text-transform:uppercase;color:var(--text-muted);text-align:center}

.iphone-frame{width:200px;height:432px;background:#1a1d2a;border-radius:36px;border:3px solid rgba(255,255,255,.12);position:relative;z-index:1;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.5);padding:0;cursor:zoom-in;font:inherit;color:inherit;transition:transform .4s cubic-bezier(.16,1,.3,1),box-shadow .4s,border-color .3s}
.iphone-frame:focus-visible{outline:2px solid var(--accent);outline-offset:6px}
@media(hover:hover) and (pointer:fine){.iphone-frame:hover{transform:scale(1.05);border-color:rgba(184,200,255,.3)}}
.iphone-notch{position:absolute;top:10px;left:50%;transform:translateX(-50%);width:80px;height:22px;background:#0d0f16;border-radius:14px;z-index:10}
.iphone-screen{position:absolute;top:3px;left:3px;right:3px;bottom:3px;border-radius:33px;overflow:hidden;background:#000}
.iphone-screen video{width:100%;height:100%;object-fit:cover;display:block}
.iphone-home-bar{position:absolute;bottom:8px;left:50%;transform:translateX(-50%);width:100px;height:4px;background:rgba(255,255,255,.3);border-radius:3px;z-index:10}

/* T4 : scrim opaque renforcé (.96) pour isoler nettement le contenu agrandi du fond. */
.video-modal{position:fixed;inset:0;z-index:200;display:flex;align-items:center;justify-content:center;padding:2rem;background:rgba(4,5,8,.96);backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px)}
.video-modal[hidden]{display:none}
.video-modal-dialog{position:relative;display:flex;flex-direction:column;align-items:center;gap:1.2rem;max-width:100%;max-height:100%}
/* T4 : surface contrastée + halo/bordure autour de la maquette agrandie (détache du fond sombre). */
.video-modal-frame{position:relative;width:min(320px,80vw);height:min(692px,calc(80vw * 2.16));max-height:85vh;cursor:default;border-radius:44px;border:1px solid rgba(184,200,255,.22);box-shadow:0 0 0 1px rgba(0,0,0,.6),0 30px 90px rgba(0,0,0,.7),0 0 80px rgba(160,180,245,.12)}
.video-modal-close{position:absolute;top:-3.2rem;right:-.2rem;width:42px;height:42px;border-radius:50%;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);color:var(--text-primary);font-size:1.1rem;line-height:1;cursor:pointer;display:flex;align-items:center;justify-content:center;font-family:var(--sans);transition:background .2s,border-color .2s,transform .2s}
.video-modal-close:hover{background:rgba(255,255,255,.14);border-color:var(--accent);transform:scale(1.08)}
.video-modal-close:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.video-modal-caption{font-family:var(--mono);font-size:.72rem;letter-spacing:.15em;text-transform:uppercase;color:var(--text-secondary);text-align:center}
body.modal-open{overflow:hidden}
@media(max-width:540px){.video-modal{padding:1rem}.video-modal-close{top:-3rem;right:0}}
@media(max-width:768px){.project-card{grid-template-columns:1fr}.project-visual{min-height:340px}}

/* footer */
footer{padding:2.4rem 3rem;display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--border);flex-wrap:wrap;gap:1rem}
.footer-brand{font-family:var(--serif);font-size:.9rem;color:var(--text-muted)}
.footer-brand .wordmark{color:var(--text-primary)}
.footer-copy{font-size:.75rem;color:var(--text-muted)}
.footer-links{display:flex;gap:1.5rem}
.footer-links a{color:var(--text-muted);text-decoration:none;font-size:.75rem;transition:color .3s}
.footer-links a:hover{color:var(--text-primary)}

@media(max-width:1024px){.card-grid.cols-4{grid-template-columns:repeat(2,1fr)}.card-grid.cols-3{grid-template-columns:1fr}}
@media(max-width:768px){header nav{padding:1.1rem 1.4rem}section{padding:4.5rem 1.4rem}.legal{padding-top:7rem}.hero{padding:7.5rem 1.4rem 3.5rem}.card-grid.cols-2,.card-grid.cols-4{grid-template-columns:1fr}section::after{left:1.4rem;right:1.4rem}footer{flex-direction:column;text-align:center}}
@media(max-width:480px){.nav-links{display:none}.hero-cta,.collaborate-cta{flex-direction:column;align-items:flex-start}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important;scroll-behavior:auto!important}}
`;
