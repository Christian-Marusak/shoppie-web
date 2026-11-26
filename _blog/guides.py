"""Návody Shoppie – generuje {sk,cs,en}/navody/ zo súborov _navody/*.json.

Volá ho _blog/build.py (python3 _blog/build.py). Formát návodu:
{
  "id": "zdielat-zoznam", "order": 7, "group": "family", "updated": "RRRR-MM-DD",
  "related": ["odobrat-clena"],
  "langs": { "sk": { "slug", "title", "description", "keywords": [...], "summary",
                     "steps": [{"title", "text" (HTML), "img": "07-1" (voliteľné)}],
                     "faq": [{"q", "a"}] }, "cs": {...}, "en": {...} }
}
Screenshot kroku: assets/navody/<img>-<jazyk>.webp (ak chýba, krok sa zobrazí bez obrázka).
"""
import json
import re
import sys
from pathlib import Path

import build as b

SRC = b.ROOT / "_navody"
IMG = b.ROOT / "assets" / "navody"
e = b.e

G = {
    "sk": dict(nav="Návody", title="Návody – Shoppie", h1="Návody",
               desc="Krátke návody krok za krokom: ako používať nákupný zoznam Shoppie na iPhone – zdieľanie s rodinou, sken bločku, Spotreba, záruky a ďalšie.",
               lead="Krátke návody krok za krokom, ako z aplikácie Shoppie vyťažiť čo najviac.",
               step="Krok", steps="krokov", steps_few="kroky", updated="Aktualizované", summary="Stručne",
               faq="Časté otázky", related="Súvisiace návody", back="Všetky návody",
               shot="Snímka obrazovky", more="Ďalšie otázky nájdete na stránke", support="Podpora",
               groups={"list": "Nákupný zoznam", "family": "Rodina a domácnosť", "receipts": "Bločky",
                       "pantry": "Spotreba a pripomienky", "warranties": "Záruky", "other": "Ostatné"}),
    "cs": dict(nav="Návody", title="Návody – Shoppie", h1="Návody",
               desc="Krátké návody krok za krokem: jak používat nákupní seznam Shoppie na iPhonu – sdílení s rodinou, sken účtenky, Spotřeba, záruky a další.",
               lead="Krátké návody krok za krokem, jak z aplikace Shoppie vytěžit co nejvíc.",
               step="Krok", steps="kroků", steps_few="kroky", updated="Aktualizováno", summary="Stručně",
               faq="Časté otázky", related="Související návody", back="Všechny návody",
               shot="Snímek obrazovky", more="Další otázky najdete na stránce", support="Podpora",
               groups={"list": "Nákupní seznam", "family": "Rodina a domácnost", "receipts": "Účtenky",
                       "pantry": "Spotřeba a připomínky", "warranties": "Záruky", "other": "Ostatní"}),
    "en": dict(nav="Guides", title="Guides – Shoppie", h1="Guides",
               desc="Short step-by-step guides on using the Shoppie shopping list on iPhone – family sharing, receipt scanning, Pantry, warranties and more.",
               lead="Short step-by-step guides to get the most out of Shoppie.",
               step="Step", steps="steps", steps_few="steps", updated="Updated", summary="In short",
               faq="Frequently asked questions", related="Related guides", back="All guides",
               shot="Screenshot", more="More questions are answered on the", support="Support page",
               groups={"list": "Shopping list", "family": "Family and household", "receipts": "Receipts",
                       "pantry": "Pantry and reminders", "warranties": "Warranties", "other": "Other"}),
}
GROUP_ORDER = ("list", "family", "receipts", "pantry", "warranties", "other")
ALLOWED = {"p", "ul", "ol", "li", "strong", "em", "a", "br", "kbd"}


def load():
    guides = []
    for f in sorted(SRC.glob("*.json")):
        g = json.loads(f.read_text(encoding="utf-8"))
        for l in b.LANGS:
            L = g["langs"].get(l)
            if not L:
                sys.exit(f"{f.name}: chýba jazyk {l}")
            for k in ("slug", "title", "description", "summary", "steps"):
                if not L.get(k):
                    sys.exit(f"{f.name}/{l}: chýba {k}")
        guides.append(g)
    guides.sort(key=lambda g: g["order"])
    return guides


def url(g, lang):
    return f"{b.SITE}/{lang}/navody/{g['langs'][lang]['slug']}.html"


def shot(img, lang):
    if not img:
        return None
    f = IMG / f"{img}-{lang}.webp"
    if not f.is_file():
        return None
    from PIL import Image
    w, h = Image.open(f).size
    return f"assets/navody/{f.name}", w, h


def n_steps(n, lang):
    t = G[lang]
    if lang == "en":
        return f"{n} {t['steps']}"
    return f"{n} {t['steps_few'] if 2 <= n <= 4 else t['steps']}"


def build_guide(g, lang, by_id):
    t, L = G[lang], g["langs"][lang]
    canonical = url(g, lang)
    alternates = {l: url(g, l) for l in b.LANGS}
    alt_rel = {l: f"../../{l}/navody/{g['langs'][l]['slug']}.html" for l in b.LANGS}
    steps_html, ld_steps, first_img = [], [], None
    for i, s in enumerate(L["steps"], 1):
        im = shot(s.get("img"), lang)
        fig = ""
        if im:
            first_img = first_img or im
            fig = (f'\n          <figure class="howto-shot"><img src="../../{im[0]}" alt="{e(t["shot"])}: {e(s["title"])}" '
                   f'width="{im[1]}" height="{im[2]}" loading="lazy"></figure>')
        steps_html.append(f'''
        <li class="howto-step" id="krok-{i}">
          <h2><span class="howto-num">{t['step']} {i}</span> {e(s['title'])}</h2>
          <div class="howto-text">{s['text']}</div>{fig}
        </li>''')
        st = {"@type": "HowToStep", "position": i, "name": s["title"],
              "text": re.sub(r"<[^>]+>", "", s["text"]).strip(), "url": f"{canonical}#krok-{i}"}
        if im:
            st["image"] = f"{b.SITE}/{im[0]}"
        ld_steps.append(st)
    faq = L.get("faq") or []
    ld = [{"@context": "https://schema.org", "@type": "HowTo", "name": L["title"], "description": L["description"],
           "inLanguage": lang, "step": ld_steps,
           "tool": {"@type": "HowToTool", "name": "iPhone + Shoppie"}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": b.T[lang]["home"], "item": f"{b.SITE}/{lang}/"},
              {"@type": "ListItem", "position": 2, "name": t["h1"], "item": f"{b.SITE}/{lang}/navody/"},
              {"@type": "ListItem", "position": 3, "name": L["title"], "item": canonical}]}]
    if first_img:
        ld[0]["image"] = f"{b.SITE}/{first_img[0]}"
    if faq:
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q["q"],
             "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", q["a"])}} for q in faq]})
    extra = "".join(b.jsonld(x) for x in ld)
    faq_html = ""
    if faq:
        items = "".join(f'\n        <details><summary>{e(q["q"])}</summary><div class="answer"><p>{q["a"]}</p></div></details>' for q in faq)
        faq_html = f'\n      <section class="post-faq" aria-labelledby="faq-h">\n        <h2 id="faq-h">{t["faq"]}</h2>\n        <div class="card faq">{items}\n        </div>\n      </section>'
    rel = [by_id[r] for r in g.get("related", []) if r in by_id]
    rel_html = ""
    if rel:
        lis = "".join(f'<li><a href="{r["langs"][lang]["slug"]}.html">{e(r["langs"][lang]["title"])}</a></li>' for r in rel)
        rel_html = f'\n      <nav class="howto-related" aria-labelledby="rel-h"><h2 id="rel-h">{t["related"]}</h2><ul>{lis}</ul></nav>'
    upd = g.get("updated")
    meta = f'{t["updated"]} <time datetime="{upd}">{b.fmt_date(upd, lang)}</time> · ' if upd else ""
    return b.head(lang, f'{L["title"]} – Shoppie', L["description"], canonical, alternates, "article", extra) + \
        b.header(lang, "guides", alt_rel, "../") + f"""
<main id="main" class="page post howto">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="../">{b.T[lang]['home']}</a> › <a href="./">{t['h1']}</a> › {e(t['groups'][g['group']])}</nav>
    <article>
      <h1>{e(L['title'])}</h1>
      <p class="meta">{meta}{n_steps(len(L['steps']), lang)}</p>
      <aside class="post-summary" aria-label="{t['summary']}"><h2>{t['summary']}</h2><p>{L['summary']}</p></aside>
      <ol class="howto-steps">{''.join(steps_html)}
      </ol>{faq_html}{rel_html}
      <p class="howto-more">{t['more']} <a href="../support.html">{t['support']}</a>.</p>
      <aside class="post-cta">
        <img src="../../assets/logo.svg" data-xmas="../../assets/img/xmas/icon-christmas.png" alt="" width="64" height="64">
        <div><h2>{b.T[lang]['cta_h']}</h2><p>{b.T[lang]['cta_p']}</p></div>
        {b.badge(lang, '../../')}
      </aside>
    </article>
    <p class="post-back"><a href="./">← {t['back']}</a></p>
  </div>
</main>
""" + b.footer(lang, "../") + "\n</body>\n</html>\n"


def build_hub(guides, lang):
    t = G[lang]
    canonical = f"{b.SITE}/{lang}/navody/"
    alternates = {l: f"{b.SITE}/{l}/navody/" for l in b.LANGS}
    alt_rel = {l: f"../../{l}/navody/" for l in b.LANGS}
    sections = []
    for grp in GROUP_ORDER:
        gs = [g for g in guides if g["group"] == grp]
        if not gs:
            continue
        cards = "".join(f"""
          <li><a class="card howto-card" href="{g['langs'][lang]['slug']}.html"><h3>{e(g['langs'][lang]['title'])}</h3><p>{e(g['langs'][lang]['description'])}</p></a></li>""" for g in gs)
        sections.append(f"""
    <section class="howto-group" aria-labelledby="g-{grp}">
      <h2 id="g-{grp}">{t['groups'][grp]}</h2>
      <ul class="howto-list">{cards}
      </ul>
    </section>""")
    ld = b.jsonld({"@context": "https://schema.org", "@type": "ItemList", "name": t["title"],
                   "itemListElement": [{"@type": "ListItem", "position": i, "url": url(g, lang),
                                        "name": g["langs"][lang]["title"]} for i, g in enumerate(guides, 1)]})
    return b.head(lang, t["title"], t["desc"], canonical, alternates, "website", ld) + \
        b.header(lang, "guides", alt_rel, "../") + f"""
<main id="main" class="page howto-hub">
  <div class="wrap">
    <h1>{t['h1']}</h1>
    <p class="lead">{t['lead']}</p>{''.join(sections)}
  </div>
</main>
""" + b.footer(lang, "../") + "\n</body>\n</html>\n"


def build_all():
    guides = load()
    if not guides:
        return [], {}
    by_id = {g["id"]: g for g in guides}
    for lang in b.LANGS:
        d = b.ROOT / lang / "navody"
        d.mkdir(parents=True, exist_ok=True)
        keep = {"index.html"}
        for g in guides:
            name = g["langs"][lang]["slug"] + ".html"
            keep.add(name)
            (d / name).write_text(build_guide(g, lang, by_id), encoding="utf-8")
        for f in d.glob("*.html"):
            if f.name not in keep:
                f.unlink()
        (d / "index.html").write_text(build_hub(guides, lang), encoding="utf-8")
    groups = [{l: f"{b.SITE}/{l}/navody/" for l in b.LANGS}]
    groups += [{l: url(g, l) for l in b.LANGS} for g in guides]
    return groups, {url(g, l): g.get("updated") for g in guides for l in b.LANGS if g.get("updated")}
