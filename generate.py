"""
generate.py — DRC Horizon
Appelle l'API Claude avec recherche web, génère index.html avec les dernières actualités.
"""
import anthropic
import json
import os
import re
from datetime import datetime

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

now_fr = datetime.utcnow().strftime("%A %d %B %Y").capitalize()
now_iso = datetime.utcnow().strftime("%d/%m/%Y à %H:%M")

print(f"[DRC Horizon] Recherche des actualités – {now_iso} UTC")

# ── 1. Appel API avec recherche web ──────────────────────────────────────────
messages = [{"role": "user", "content": f"""Date actuelle : {now_fr}.
Recherche sur internet les 6 actualités les plus importantes et récentes
sur la République Démocratique du Congo (RDC / Congo-Kinshasa).

Réponds UNIQUEMENT avec un objet JSON valide (sans markdown, sans backtick) :
{{
  "ticker": ["flash info 1","flash info 2","flash info 3","flash info 4"],
  "articles": [
    {{
      "id": 1,
      "titre": "Titre accrocheur 8-12 mots",
      "resume": "Résumé factuel en 2 phrases, max 200 caractères.",
      "contenu": "3 paragraphes factuels et contextualisés sur cet article, ~250 mots.",
      "categorie": "Politique",
      "source": "Nom de la source",
      "source_url": "https://...",
      "date": "12 mai 2026",
      "hashtags": ["#RDC","#Congo","#DRC"],
      "urgence": "haute"
    }}
  ]
}}

Catégories possibles : Politique, Sécurité, Humanitaire, Économie, Diplomatie, Société.
urgence = "haute" seulement pour les 2 sujets les plus importants.
"""}]

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=3000,
    tools=[{"type": "web_search_20250305", "name": "web_search"}],
    messages=messages,
)

# ── 2. Extraire le JSON ───────────────────────────────────────────────────────
text = ""
for block in response.content:
    if block.type == "text":
        text = block.text
        break

text = text.strip()
text = re.sub(r"```json\n?", "", text)
text = re.sub(r"```\n?", "", text)

data = json.loads(text)
articles = data.get("articles", [])
ticker_items = data.get("ticker", ["Actualités RDC en direct"])

print(f"[DRC Horizon] {len(articles)} articles récupérés.")

# ── 3. Helpers HTML ───────────────────────────────────────────────────────────
CAT_CLASSES = {
    "Politique":   ("cat-politique",   "#1E3A8A", "#DBEAFE"),
    "Sécurité":    ("cat-securite",    "#7F1D1D", "#FEE2E2"),
    "Humanitaire": ("cat-humanitaire", "#065F46", "#D1FAE5"),
    "Économie":    ("cat-economie",    "#78350F", "#FEF3C7"),
    "Diplomatie":  ("cat-diplomatie",  "#134E4A", "#CCFBF1"),
    "Société":     ("cat-societe",     "#4C1D95", "#EDE9FE"),
}
THUMB_GRADIENTS = [
    "linear-gradient(135deg,#134E4A,#065F46)",
    "linear-gradient(135deg,#1E3A8A,#003080)",
    "linear-gradient(135deg,#78350F,#92400E)",
    "linear-gradient(135deg,#7F1D1D,#991B1B)",
    "linear-gradient(135deg,#065F46,#047857)",
    "linear-gradient(135deg,#4C1D95,#5B21B6)",
]

def cat_class(name):
    return CAT_CLASSES.get(name, ("cat-politique", "#1E3A8A", "#DBEAFE"))

def ticker_html(items):
    content = " &nbsp;&nbsp;·&nbsp;&nbsp; ".join(items) * 2
    return f'<div class="ticker">&nbsp;&nbsp;·&nbsp;&nbsp; {content} &nbsp;&nbsp;·&nbsp;&nbsp;</div>'

def featured_card_html(art):
    cls, _, _ = cat_class(art["categorie"])
    urgent = '<div class="urgence-banner">🔴 URGENT</div>' if art.get("urgence") == "haute" else ""
    contenu_json = json.dumps(art.get("contenu",""), ensure_ascii=False)
    return f"""
<div class="featured-card" onclick="openArticle({art['id']})">
  <div class="featured-img" style="background:linear-gradient(135deg,#002B6B 0%,#003080 100%);">
    <div class="featured-img-inner">
      <svg width="64" height="46" viewBox="0 0 64 46"><path d="M16 23 A16 16 0 0 1 48 23" fill="#F7D418"/><circle cx="32" cy="23" r="10" fill="#F7D418"/><line x1="3" y1="23" x2="61" y2="23" stroke="white" stroke-width="2.5" stroke-linecap="round"/></svg>
    </div>
    <div class="featured-img-flag"><span style="background:#007FFF"></span><span style="background:#F7D418"></span><span style="background:#CE1126"></span></div>
  </div>
  <div class="featured-body">
    {urgent}
    <div class="featured-meta">
      <span class="cat {cls}">{art["categorie"]}</span>
      <span class="featured-date">{art["date"]}</span>
    </div>
    <div class="featured-title">{art["titre"]}</div>
    <div class="featured-excerpt">{art["resume"]}</div>
    <div class="featured-source">📰 Source : {art["source"]}</div>
  </div>
</div>"""

def mini_card_html(art, num):
    cls, _, _ = cat_class(art["categorie"])
    return f"""
<div class="mini-card" onclick="openArticle({art['id']})">
  <div class="mini-num">{num:02d}</div>
  <div class="mini-content">
    <div class="featured-meta" style="margin-bottom:6px"><span class="cat {cls}">{art["categorie"]}</span></div>
    <div class="mini-title">{art["titre"]}</div>
    <div class="mini-source">{art["source"]} · {art["date"]}</div>
  </div>
</div>"""

def article_card_html(art, idx):
    cls, _, _ = cat_class(art["categorie"])
    grad = THUMB_GRADIENTS[idx % len(THUMB_GRADIENTS)]
    return f"""
<div class="article-card" onclick="openArticle({art['id']})">
  <div class="article-thumb" style="background:{grad};">
    <svg width="48" height="34" viewBox="0 0 48 34"><path d="M12 17 A12 12 0 0 1 36 17" fill="#F7D418"/><circle cx="24" cy="17" r="7.5" fill="#F7D418"/><line x1="2" y1="17" x2="46" y2="17" stroke="white" stroke-width="2" stroke-linecap="round"/></svg>
    <div class="article-thumb-flag"><span style="background:#007FFF"></span><span style="background:#F7D418"></span><span style="background:#CE1126"></span></div>
  </div>
  <div class="article-body">
    <div class="article-meta"><span class="cat {cls}">{art["categorie"]}</span><span class="article-date">{art["date"]}</span></div>
    <div class="article-title">{art["titre"]}</div>
    <div class="article-excerpt">{art["resume"]}</div>
    <div class="article-source">📰 {art["source"]}</div>
  </div>
</div>"""

# ── 4. Données JS pour les modals ─────────────────────────────────────────────
def articles_js(arts):
    return "const ARTICLES = " + json.dumps(arts, ensure_ascii=False) + ";"

# ── 5. Générer le HTML ────────────────────────────────────────────────────────
featured = articles[0] if articles else {}
side_arts = articles[1:5] if len(articles) > 1 else []
grid_arts = articles if len(articles) >= 1 else []

featured_html  = featured_card_html(featured) if featured else ""
mini_cards_html = "\n".join(mini_card_html(a, i+1) for i, a in enumerate(side_arts))
article_grid_html = "\n".join(article_card_html(a, i) for i, a in enumerate(grid_arts))

html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DRC Horizon — Actualités République Démocratique du Congo</title>
<meta name="description" content="Actualités politiques, sécuritaires, économiques et humanitaires de la RDC. DRC Horizon – @HorizonActu">
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Source+Sans+3:wght@300;400;600;700&display=swap');
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--blue:#007FFF;--yellow:#F7D418;--red:#CE1126;--navy:#002B6B;--dark:#00112E;--sky:#003080;--text:#1a1a2e;--muted:#6B7280;--bg:#F5F7FA;--card:#fff;--border:#E5EBF2;--serif:'Playfair Display',Georgia,serif;--sans:'Source Sans 3','Helvetica Neue',Arial,sans-serif}}
body{{font-family:var(--sans);background:var(--bg);color:var(--text);line-height:1.6}}
::-webkit-scrollbar{{width:6px}}::-webkit-scrollbar-thumb{{background:var(--navy);border-radius:3px}}
.topbar{{background:var(--dark);padding:7px 0;font-size:11px;color:rgba(255,255,255,.45);letter-spacing:.5px;border-bottom:1px solid rgba(255,255,255,.06)}}
.topbar .inner{{display:flex;justify-content:space-between;align-items:center}}
.topbar a{{color:var(--yellow);text-decoration:none;margin-left:16px}}
nav{{background:var(--dark);position:sticky;top:0;z-index:100;border-bottom:3px solid transparent;border-image:linear-gradient(to right,var(--blue) 33%,var(--yellow) 33%,var(--yellow) 66%,var(--red) 66%) 1}}
.nav-inner{{display:flex;align-items:center;justify-content:space-between;height:64px}}
.brand{{display:flex;align-items:center;gap:14px;text-decoration:none}}
.brand-name{{font-family:var(--serif);font-size:21px;font-weight:700;color:#fff;line-height:1}}
.brand-sub{{font-size:10px;color:rgba(255,255,255,.38);letter-spacing:1.8px;text-transform:uppercase;margin-top:2px}}
.nav-links{{display:flex;gap:0}}
.nav-links a{{color:rgba(255,255,255,.6);text-decoration:none;font-size:12px;font-weight:600;letter-spacing:.5px;padding:0 16px;height:64px;display:flex;align-items:center;transition:color .2s,background .2s;text-transform:uppercase}}
.nav-links a:hover,.nav-links a.active{{color:var(--yellow);background:rgba(247,212,24,.06)}}
.nav-cta{{background:var(--yellow)!important;color:var(--dark)!important;border-radius:6px;padding:0 18px!important;font-weight:700!important}}
.container{{max-width:1180px;margin:0 auto;padding:0 24px}}
.hero{{background:var(--dark);padding:64px 0 52px;position:relative;overflow:hidden}}
.hero::before{{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 60% 120%,var(--sky) 0%,transparent 65%)}}
.hero-inner{{position:relative;display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:center}}
.hero-label{{font-size:11px;font-weight:700;letter-spacing:2px;color:var(--yellow);text-transform:uppercase;margin-bottom:14px}}
.hero h1{{font-family:var(--serif);font-size:44px;font-weight:800;color:#fff;line-height:1.15;letter-spacing:-.5px;margin-bottom:18px}}
.hero-desc{{font-size:15px;color:rgba(255,255,255,.6);line-height:1.75;margin-bottom:28px}}
.hero-actions{{display:flex;gap:12px;flex-wrap:wrap}}
.btn-primary{{background:var(--yellow);color:var(--dark);font-weight:700;font-size:13px;padding:11px 24px;border-radius:7px;text-decoration:none;transition:background .2s,transform .15s;display:inline-flex;align-items:center;gap:6px}}
.btn-primary:hover{{background:#e6c300;transform:translateY(-1px)}}
.btn-ghost{{border:1px solid rgba(255,255,255,.2);color:rgba(255,255,255,.75);font-size:13px;padding:11px 24px;border-radius:7px;text-decoration:none;transition:all .2s}}
.btn-ghost:hover{{border-color:rgba(255,255,255,.5);color:#fff}}
.hero-stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}
.stat-card{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:18px 20px;text-align:center}}
.stat-num{{font-family:var(--serif);font-size:28px;font-weight:700;color:var(--yellow);line-height:1}}
.stat-label{{font-size:11px;color:rgba(255,255,255,.4);margin-top:4px;letter-spacing:.5px}}
.stat-featured{{grid-column:span 3;background:rgba(247,212,24,.06);border-color:rgba(247,212,24,.2)}}
.live-dot{{display:inline-block;width:7px;height:7px;background:var(--red);border-radius:50%;margin-right:6px;animation:pulse 1.8s infinite}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.5;transform:scale(1.3)}}}}
.breaking{{background:var(--red);padding:10px 0;overflow:hidden}}
.breaking-inner{{display:flex;align-items:center;gap:16px}}
.breaking-badge{{background:#fff;color:var(--red);font-size:10px;font-weight:800;padding:3px 10px;border-radius:3px;letter-spacing:1px;text-transform:uppercase;white-space:nowrap}}
.ticker-wrap{{overflow:hidden;flex:1}}
.ticker{{display:inline-flex;animation:ticker 32s linear infinite;white-space:nowrap;font-size:13px;color:#fff;font-weight:600}}
.ticker:hover{{animation-play-state:paused}}
@keyframes ticker{{0%{{transform:translateX(0)}}100%{{transform:translateX(-50%)}}}}
.section{{padding:52px 0}}
.section-header{{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:28px;padding-bottom:14px;border-bottom:2px solid var(--border)}}
.section-title{{font-family:var(--serif);font-size:22px;font-weight:700;color:var(--dark)}}
.section-title span{{color:var(--blue)}}
.see-all{{font-size:12px;font-weight:700;color:var(--blue);text-decoration:none}}
.cat{{display:inline-block;font-size:9px;font-weight:700;padding:3px 10px;border-radius:20px;text-transform:uppercase;letter-spacing:1px}}
.cat-politique{{background:#DBEAFE;color:#1E3A8A}}.cat-securite{{background:#FEE2E2;color:#7F1D1D}}.cat-humanitaire{{background:#D1FAE5;color:#065F46}}.cat-economie{{background:#FEF3C7;color:#78350F}}.cat-societe{{background:#EDE9FE;color:#4C1D95}}.cat-diplomatie{{background:#CCFBF1;color:#134E4A}}
.main-grid{{display:grid;grid-template-columns:2fr 1fr;gap:32px}}
.featured-card{{background:var(--card);border-radius:12px;overflow:hidden;border:1px solid var(--border);transition:transform .2s,box-shadow .2s;cursor:pointer}}
.featured-card:hover{{transform:translateY(-3px);box-shadow:0 12px 32px rgba(0,0,0,.1)}}
.featured-img{{height:240px;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden}}
.featured-img-inner{{text-align:center}}
.featured-img-flag{{display:flex;height:8px;position:absolute;bottom:0;left:0;right:0}}
.featured-img-flag span{{flex:1}}
.urgence-banner{{background:var(--red);padding:4px 14px;color:#fff;font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase}}
.featured-body{{padding:22px 24px}}
.featured-meta{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
.featured-date{{font-size:11px;color:var(--muted)}}
.featured-title{{font-family:var(--serif);font-size:22px;font-weight:700;color:var(--dark);line-height:1.3;margin-bottom:10px}}
.featured-excerpt{{font-size:13px;color:var(--muted);line-height:1.7}}
.featured-source{{font-size:11px;color:var(--muted);margin-top:14px;padding-top:14px;border-top:1px solid var(--border)}}
.card-list{{display:flex;flex-direction:column;gap:14px}}
.mini-card{{background:var(--card);border-radius:10px;padding:16px 18px;border:1px solid var(--border);display:flex;gap:14px;align-items:flex-start;transition:transform .2s,border-color .2s;cursor:pointer}}
.mini-card:hover{{transform:translateX(3px);border-color:var(--blue)}}
.mini-num{{font-family:var(--serif);font-size:26px;font-weight:800;color:var(--border);line-height:1;flex-shrink:0;width:28px;transition:color .2s}}
.mini-card:hover .mini-num{{color:var(--blue)}}
.mini-title{{font-size:13px;font-weight:700;color:var(--dark);line-height:1.4;margin-bottom:5px}}
.mini-source{{font-size:10px;color:var(--muted)}}
.cat-filter{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:28px}}
.cat-pill{{padding:7px 16px;border-radius:20px;font-size:12px;font-weight:600;border:1px solid var(--border);background:var(--card);color:var(--muted);cursor:pointer;transition:all .2s;text-decoration:none}}
.cat-pill:hover,.cat-pill.active{{background:var(--blue);color:#fff;border-color:var(--blue)}}
.article-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}}
.article-card{{background:var(--card);border-radius:10px;border:1px solid var(--border);overflow:hidden;transition:transform .2s,box-shadow .2s;cursor:pointer}}
.article-card:hover{{transform:translateY(-4px);box-shadow:0 12px 28px rgba(0,0,0,.09)}}
.article-thumb{{height:140px;display:flex;align-items:center;justify-content:center;position:relative}}
.article-thumb-flag{{position:absolute;bottom:0;left:0;right:0;height:4px;display:flex}}
.article-thumb-flag span{{flex:1}}
.article-body{{padding:16px 18px 18px}}
.article-meta{{display:flex;align-items:center;gap:8px;margin-bottom:8px}}
.article-date{{font-size:10px;color:var(--muted)}}
.article-title{{font-family:var(--serif);font-size:15px;font-weight:700;color:var(--dark);line-height:1.35;margin-bottom:8px}}
.article-excerpt{{font-size:12px;color:var(--muted);line-height:1.65}}
.article-source{{font-size:10px;color:var(--muted);margin-top:12px;padding-top:10px;border-top:1px solid var(--border)}}
.nl-band{{background:var(--dark);padding:52px 0;position:relative;overflow:hidden}}
.nl-band::before{{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 30% 50%,var(--sky) 0%,transparent 60%)}}
.nl-inner{{position:relative;display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:center}}
.nl-title{{font-family:var(--serif);font-size:30px;font-weight:700;color:#fff;margin-bottom:12px;line-height:1.25}}
.nl-sub{{font-size:14px;color:rgba(255,255,255,.55);line-height:1.7}}
.nl-form{{display:flex;gap:10px}}
.nl-input{{flex:1;padding:13px 18px;border-radius:8px;border:1px solid rgba(255,255,255,.15);background:rgba(255,255,255,.08);color:#fff;font-size:13px;font-family:var(--sans);outline:none}}
.nl-input:focus{{border-color:var(--yellow)}}
.nl-submit{{background:var(--yellow);color:var(--dark);font-weight:700;font-size:13px;padding:13px 22px;border-radius:8px;border:none;cursor:pointer;font-family:var(--sans);transition:background .2s;white-space:nowrap}}
.social-band{{background:var(--card);border-top:1px solid var(--border);border-bottom:1px solid var(--border);padding:28px 0}}
.social-inner{{display:flex;align-items:center;justify-content:center;gap:16px;flex-wrap:wrap}}
.social-btn{{display:flex;align-items:center;gap:8px;padding:10px 20px;border-radius:8px;font-size:12px;font-weight:700;text-decoration:none;transition:transform .15s,box-shadow .15s}}
.social-btn:hover{{transform:translateY(-2px);box-shadow:0 4px 14px rgba(0,0,0,.12)}}
.social-insta{{background:#E1306C;color:#fff}}.social-fb{{background:#1877F2;color:#fff}}.social-x{{background:#000;color:#fff}}
footer{{background:var(--dark);padding:44px 0 28px}}
.footer-grid{{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:40px;margin-bottom:40px}}
.footer-brand-name{{font-family:var(--serif);font-size:20px;font-weight:700;color:#fff;margin-bottom:10px}}
.footer-brand-desc{{font-size:12px;color:rgba(255,255,255,.4);line-height:1.8}}
.footer-col-title{{font-size:11px;font-weight:700;letter-spacing:1.5px;color:var(--yellow);text-transform:uppercase;margin-bottom:14px}}
.footer-links{{list-style:none}}
.footer-links li{{margin-bottom:8px}}
.footer-links a{{font-size:12px;color:rgba(255,255,255,.45);text-decoration:none;transition:color .2s}}
.footer-links a:hover{{color:#fff}}
.footer-bottom{{border-top:1px solid rgba(255,255,255,.08);padding-top:20px;display:flex;justify-content:space-between;align-items:center}}
.footer-copy{{font-size:11px;color:rgba(255,255,255,.3)}}
.footer-flag{{display:flex;height:3px;width:80px;border-radius:2px;overflow:hidden}}
.footer-flag span:nth-child(1){{flex:1;background:var(--blue)}}.footer-flag span:nth-child(2){{flex:1;background:var(--yellow)}}.footer-flag span:nth-child(3){{flex:1;background:var(--red)}}
/* ── MODAL ── */
.modal-overlay{{position:fixed;inset:0;background:rgba(0,0,30,.75);z-index:999;display:flex;align-items:flex-end;justify-content:center;opacity:0;pointer-events:none;transition:opacity .3s}}
.modal-overlay.open{{opacity:1;pointer-events:all}}
.modal-drawer{{background:#fff;width:100%;max-width:720px;max-height:90vh;overflow-y:auto;border-radius:16px 16px 0 0;padding:32px;transform:translateY(40px);transition:transform .35s cubic-bezier(.22,.8,.3,1)}}
.modal-overlay.open .modal-drawer{{transform:translateY(0)}}
.modal-close{{float:right;background:var(--bg);border:none;border-radius:50%;width:34px;height:34px;font-size:18px;cursor:pointer;line-height:34px;text-align:center;color:var(--muted);transition:background .2s}}
.modal-close:hover{{background:var(--border)}}
.modal-cat{{display:inline-block;font-size:9px;font-weight:700;padding:3px 10px;border-radius:20px;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}}
.modal-title{{font-family:var(--serif);font-size:26px;font-weight:800;color:var(--dark);line-height:1.25;margin-bottom:12px}}
.modal-meta{{font-size:12px;color:var(--muted);margin-bottom:20px;padding-bottom:18px;border-bottom:1px solid var(--border)}}
.modal-body p{{font-size:14px;color:var(--text);line-height:1.8;margin-bottom:14px}}
.modal-footer{{margin-top:24px;padding-top:18px;border-top:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}}
.btn-source{{background:var(--navy);color:#fff;font-size:12px;font-weight:700;padding:10px 20px;border-radius:7px;text-decoration:none;transition:background .2s}}
.btn-source:hover{{background:var(--sky)}}
.modal-hashtags{{display:flex;gap:6px;flex-wrap:wrap}}
.modal-hashtags span{{font-size:11px;font-weight:700;color:var(--blue)}}
.updated-at{{font-size:10px;color:rgba(255,255,255,.35);text-align:right;margin-top:4px}}
@media(max-width:768px){{.hero-inner,.main-grid,.nl-inner,.footer-grid{{grid-template-columns:1fr}}.article-grid{{grid-template-columns:1fr}}.hero h1{{font-size:28px}}.nav-links{{display:none}}.hero-stats{{grid-template-columns:1fr 1fr}}.stat-featured{{grid-column:span 2}}.modal-drawer{{padding:20px}}.modal-title{{font-size:20px}}}}
</style>
</head>
<body>

<!-- DATA -->
<script>{articles_js(articles)}</script>

<!-- MODAL -->
<div class="modal-overlay" id="modal-overlay" onclick="closeModal(event)">
  <div class="modal-drawer" id="modal-drawer">
    <button class="modal-close" onclick="closeModal()">✕</button>
    <div id="modal-cat" class="modal-cat"></div>
    <div id="modal-title" class="modal-title"></div>
    <div id="modal-meta" class="modal-meta"></div>
    <div id="modal-body" class="modal-body"></div>
    <div class="modal-footer">
      <a id="modal-source-link" class="btn-source" href="#" target="_blank" rel="noopener">📰 Lire la source →</a>
      <div id="modal-hashtags" class="modal-hashtags"></div>
    </div>
  </div>
</div>

<!-- TOP BAR -->
<div class="topbar">
  <div class="container inner">
    <span>Mis à jour : {now_iso} UTC</span>
    <span>
      <a href="#">Instagram</a>
      <a href="#">Facebook</a>
      <a href="#">@HorizonActu</a>
    </span>
  </div>
</div>

<!-- NAV -->
<nav>
  <div class="container nav-inner">
    <a href="#" class="brand">
      <svg width="44" height="32" viewBox="0 0 44 32"><path d="M11 16 A11 11 0 0 1 33 16" fill="#F7D418"/><circle cx="22" cy="16" r="7" fill="#F7D418"/><line x1="2" y1="16" x2="42" y2="16" stroke="white" stroke-width="2" stroke-linecap="round"/></svg>
      <div>
        <div class="brand-name">DRC Horizon</div>
        <div class="brand-sub">@HorizonActu</div>
      </div>
    </a>
    <div class="nav-links">
      <a href="#" class="active">Accueil</a>
      <a href="#">Politique</a>
      <a href="#">Sécurité</a>
      <a href="#">Économie</a>
      <a href="#">Humanitaire</a>
      <a href="#">Newsletter</a>
      <a href="#" class="nav-cta">S'abonner</a>
    </div>
  </div>
</nav>

<!-- BREAKING -->
<div class="breaking">
  <div class="container breaking-inner">
    <div class="breaking-badge">🔴 En direct</div>
    <div class="ticker-wrap">
      {ticker_html(ticker_items)}
    </div>
  </div>
</div>

<!-- HERO -->
<section class="hero">
  <div class="container hero-inner">
    <div>
      <div class="hero-label"><span class="live-dot"></span>Actualités en temps réel — RDC</div>
      <h1>L'information congolaise, claire et fiable</h1>
      <p class="hero-desc">DRC Horizon suit l'actualité politique, sécuritaire, économique et humanitaire de la RDC pour vous tenir informés, chaque jour, sur tous vos réseaux.</p>
      <div class="hero-actions">
        <a href="#actualites" class="btn-primary">📰 Lire les dernières news</a>
        <a href="#newsletter" class="btn-ghost">S'abonner à la newsletter →</a>
      </div>
    </div>
    <div class="hero-stats">
      <div class="stat-card"><div class="stat-num">3</div><div class="stat-label">Posts / jour</div></div>
      <div class="stat-card"><div class="stat-num">7</div><div class="stat-label">Catégories</div></div>
      <div class="stat-card"><div class="stat-num">100%</div><div class="stat-label">Indépendant</div></div>
      <div class="stat-card stat-featured"><div class="stat-num" style="font-size:20px;color:#fff">🌅 DRC Horizon</div><div class="stat-label" style="margin-top:6px">Votre fenêtre sur la RDC · Instagram · Facebook · X</div></div>
    </div>
  </div>
</section>

<!-- UNE -->
<section class="section" id="actualites">
  <div class="container">
    <div class="section-header">
      <div class="section-title">À la une <span>cette semaine</span></div>
      <a href="#archive" class="see-all">Voir tout →</a>
    </div>
    <div class="main-grid">
      {featured_html}
      <div class="card-list">
        {mini_cards_html}
      </div>
    </div>
  </div>
</section>

<!-- ARCHIVE -->
<section class="section" id="archive" style="background:#fff;padding:48px 0">
  <div class="container">
    <div class="section-header">
      <div class="section-title">Archive <span>des articles</span></div>
      <span class="see-all">Mis à jour automatiquement toutes les heures</span>
    </div>
    <div class="cat-filter">
      <a href="#" class="cat-pill active">Tous</a>
      <a href="#" class="cat-pill">Politique</a>
      <a href="#" class="cat-pill">Sécurité</a>
      <a href="#" class="cat-pill">Économie</a>
      <a href="#" class="cat-pill">Humanitaire</a>
      <a href="#" class="cat-pill">Diplomatie</a>
      <a href="#" class="cat-pill">Société</a>
    </div>
    <div class="article-grid">
      {article_grid_html}
    </div>
  </div>
</section>

<!-- NEWSLETTER -->
<div class="nl-band" id="newsletter">
  <div class="container nl-inner">
    <div>
      <div style="font-size:11px;font-weight:700;letter-spacing:2px;color:rgba(247,212,24,.7);text-transform:uppercase;margin-bottom:10px">Newsletter hebdomadaire</div>
      <div class="nl-title">Restez informé.<br>Chaque vendredi,<br>l'essentiel RDC.</div>
      <div class="nl-sub">Recevez les 5 actualités clés de la semaine dans votre boîte mail.</div>
    </div>
    <div>
      <div class="nl-form">
        <input class="nl-input" type="email" placeholder="votre@email.com">
        <button class="nl-submit" onclick="alert('Merci ! Vous êtes inscrit à DRC Horizon.')">S'abonner →</button>
      </div>
      <div style="font-size:11px;color:rgba(255,255,255,.3);margin-top:8px">🔒 Pas de spam. Désabonnement en 1 clic.</div>
    </div>
  </div>
</div>

<!-- SOCIAL -->
<div class="social-band">
  <div class="container social-inner">
    <span style="font-size:13px;font-weight:700;color:var(--dark)">Suivez DRC Horizon sur</span>
    <span style="color:var(--border);font-size:20px">·</span>
    <a href="#" class="social-btn social-insta">📸 Instagram</a>
    <a href="#" class="social-btn social-fb">👍 Facebook</a>
    <a href="#" class="social-btn social-x">✕ @HorizonActu</a>
  </div>
</div>

<!-- FOOTER -->
<footer>
  <div class="container">
    <div class="footer-grid">
      <div>
        <div class="footer-brand-name">DRC Horizon</div>
        <div class="footer-brand-desc">Votre source d'information indépendante sur la République Démocratique du Congo. Politique, sécurité, économie, humanitaire — couverts chaque jour.</div>
        <div class="footer-flag" style="margin-top:16px"><span></span><span></span><span></span></div>
        <div class="updated-at">Dernière mise à jour : {now_iso} UTC</div>
      </div>
      <div>
        <div class="footer-col-title">Rubriques</div>
        <ul class="footer-links"><li><a href="#">Politique</a></li><li><a href="#">Sécurité</a></li><li><a href="#">Économie</a></li><li><a href="#">Humanitaire</a></li><li><a href="#">Diplomatie</a></li><li><a href="#">Société & Culture</a></li></ul>
      </div>
      <div>
        <div class="footer-col-title">Réseaux</div>
        <ul class="footer-links"><li><a href="#">Instagram</a></li><li><a href="#">Facebook</a></li><li><a href="#">X / Twitter</a></li><li><a href="#">Newsletter</a></li></ul>
      </div>
      <div>
        <div class="footer-col-title">À propos</div>
        <ul class="footer-links"><li><a href="#">Notre mission</a></li><li><a href="#">Contact</a></li><li><a href="#">Mentions légales</a></li><li><a href="#">Confidentialité</a></li></ul>
      </div>
    </div>
    <div class="footer-bottom">
      <div class="footer-copy">© 2026 DRC Horizon · @HorizonActu · Tous droits réservés</div>
      <div class="footer-flag"><span></span><span></span><span></span></div>
    </div>
  </div>
</footer>

<script>
const CAT_STYLES = {{
  "Politique":  {{"cls":"cat-politique","bg":"#DBEAFE","fg":"#1E3A8A"}},
  "Sécurité":   {{"cls":"cat-securite", "bg":"#FEE2E2","fg":"#7F1D1D"}},
  "Humanitaire":{{"cls":"cat-humanitaire","bg":"#D1FAE5","fg":"#065F46"}},
  "Économie":   {{"cls":"cat-economie", "bg":"#FEF3C7","fg":"#78350F"}},
  "Diplomatie": {{"cls":"cat-diplomatie","bg":"#CCFBF1","fg":"#134E4A"}},
  "Société":    {{"cls":"cat-societe",  "bg":"#EDE9FE","fg":"#4C1D95"}},
}};

function openArticle(id) {{
  const art = ARTICLES.find(a => a.id === id);
  if (!art) return;
  const cs = CAT_STYLES[art.categorie] || CAT_STYLES["Politique"];
  document.getElementById("modal-cat").textContent = art.categorie;
  document.getElementById("modal-cat").style.background = cs.bg;
  document.getElementById("modal-cat").style.color = cs.fg;
  document.getElementById("modal-title").textContent = art.titre;
  document.getElementById("modal-meta").innerHTML =
    "<strong>" + art.date + "</strong> &nbsp;·&nbsp; Source : " + art.source;
  const contenu = art.contenu || art.resume;
  document.getElementById("modal-body").innerHTML = contenu
    .split("\\n\\n").map(p => "<p>" + p + "</p>").join("");
  const srcLink = document.getElementById("modal-source-link");
  srcLink.href = art.source_url || "#";
  srcLink.textContent = "📰 Lire sur " + art.source + " →";
  document.getElementById("modal-hashtags").innerHTML =
    (art.hashtags || []).map(h => "<span>" + h + "</span>").join("");
  document.getElementById("modal-overlay").classList.add("open");
  document.body.style.overflow = "hidden";
}}

function closeModal(e) {{
  if (e && e.target !== document.getElementById("modal-overlay") && !e.target.classList.contains("modal-close")) return;
  document.getElementById("modal-overlay").classList.remove("open");
  document.body.style.overflow = "";
}}

document.addEventListener("keydown", e => {{ if (e.key === "Escape") closeModal(); }});
</script>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"[DRC Horizon] index.html généré avec succès ({len(html)} caractères).")
