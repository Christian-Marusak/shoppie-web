"""Funkcie Shoppie – generuje {sk,cs,en}/funkcie/ zo súborov _funkcie/*.json.

Volá ho _blog/build.py (python3 _blog/build.py). Formát stránky funkcie:
{
  "id": "sken-blocku", "order": 3, "icon": "receipt" (id ikony z assets/icons.svg), "updated": "RRRR-MM-DD",
  "guides": ["sken-blocku", "sken-nerozpoznal"],      # id návodov z _navody/
  "related": ["spotreba"],                             # id iných funkcií
  "shots": ["10-3", "12-1"],                           # max. 2 snímky z assets/navody/<id>-<jazyk>.webp
  "langs": { "sk": { "slug", "name" (krátky názov na kartu), "title", "description", "keywords": [...],
                     "summary", "shots_alt": ["…", "…"], "body" (HTML, h2/h3/p/ul/ol/li/strong/em/a/table…),
                     "faq": [{"q", "a"}] }, "cs": {...}, "en": {...} }
}
Pravidlá obsahu: _blog/README.md (vykanie, len funkcie zo zoznamu „Čo Shoppie naozaj vie“).
"""
import json
import re
import sys
from pathlib import Path

import build as b
import check as c

SRC = b.ROOT / "_funkcie"
IMG = b.ROOT / "assets" / "navody"
e = b.e
ALLOWED = {"p", "h2", "h3", "ul", "ol", "li", "strong", "em", "a", "table", "tr", "th", "td", "blockquote", "br"}

F = {
    "sk": dict(eyebrow="Nákupný zoznam pre iPhone", h1="Funkcie", title="Funkcie Shoppie – nákupný zoznam pre iPhone",
               desc="Čo všetko vie Shoppie: rýchly nákupný zoznam, spoločná domácnosť cez iCloud, sken bločku, "
                    "Spotreba s dátumami spotreby, záruky a ďalšie. Zadarmo a bez registrácie.",
               lead="Všetko, čo Shoppie vie – prehľadne na jednom mieste. Ku každej funkcii nájdete aj návody krok za krokom.",
               summary="Stručne", faq="Časté otázky", guides="Návody krok za krokom", related="Súvisiace funkcie",
               back="Všetky funkcie", more="Zistiť viac", updated="Aktualizované", shot="Snímka obrazovky"),
    "cs": dict(eyebrow="Nákupní seznam pro iPhone", h1="Funkce", title="Funkce Shoppie – nákupní seznam pro iPhone",
               desc="Co všechno Shoppie umí: rychlý nákupní seznam, společná domácnost přes iCloud, sken účtenky, "
                    "Spotřeba s daty spotřeby, záruky a další. Zdarma a bez registrace.",
               lead="Vše, co Shoppie umí – přehledně na jednom místě. Ke každé funkci najdete i návody krok za krokem.",
               summary="Stručně", faq="Časté otázky", guides="Návody krok za krokem", related="Související funkce",
               back="Všechny funkce", more="Zjistit víc", updated="Aktualizováno", shot="Snímek obrazovky"),
    "en": dict(eyebrow="The iPhone shopping list", h1="Features", title="Shoppie features – the iPhone shopping list",
               desc="Everything Shoppie can do: a fast shopping list, a shared household via iCloud, receipt scanning, "
                    "Pantry with best-before dates, warranties and more. Free, no sign-up.",
               lead="Everything Shoppie can do, in one place. Each feature links to step-by-step guides.",
               summary="In short", faq="Frequently asked questions", guides="Step-by-step guides",
               related="Related features", back="All features", more="Learn more", updated="Updated",
               shot="Screenshot"),
}


def validate(f, p):
    errs = []
    for k in ("id", "order", "icon", "langs"):
        if k not in p:
            errs.append(f"chýba {k}")
    for l in b.LANGS:
        L = p.get("langs", {}).get(l)
        if not L:
            errs.append(f"[{l}] chýba jazyk")
            continue
        miss = [k for k in ("slug", "name", "title", "description", "keywords", "summary", "body", "faq") if not L.get(k)]
        if miss:
            errs.append(f"[{l}] chýba {', '.join(miss)}")
            continue
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", L["slug"]):
            errs.append(f"[{l}] zlý slug")
        if len(L["title"]) > 65:
            errs.append(f"[{l}] nadpis má {len(L['title'])} znakov (max. 65)")
        if not 110 <= len(L["description"]) <= 160:
            errs.append(f"[{l}] popis má {len(L['description'])} znakov (110–160)")
        bad = {t.lower() for t in re.findall(r"</?([a-zA-Z0-9]+)", L["body"])} - ALLOWED
        if bad:
            errs.append(f"[{l}] nepovolené značky: {', '.join(sorted(bad))}")
        if re.search(r'href="[^"]*index\.html', L["body"]):
            errs.append(f"[{l}] odkaz na index.html")
        if L["body"].count("<h2") < 3:
            errs.append(f"[{l}] menej ako 3 nadpisy h2")
        full = " ".join([L["summary"], L["body"]] + [q["q"] + " " + q["a"] for q in L["faq"]])
        if l in c.TYKANIE:
            hits = sorted({m.group(0) for m in re.finditer(c.TYKANIE[l], c.text(full), re.I)})
            if hits:
                errs.append(f"[{l}] možné tykanie: {', '.join(hits)}")
        kw = L["keywords"][0].lower()
        if kw not in (L["title"] + " " + L["description"] + " " + L["summary"]).lower():
            errs.append(f"[{l}] hlavné kľúčové slovo '{kw}' nie je v nadpise, popise ani zhrnutí")
    return [f"{f.name}: {x}" for x in errs]


def load():
    feats, errs = [], []
    for f in sorted(SRC.glob("*.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        errs += validate(f, p)
        feats.append(p)
    if errs:
        sys.exit("CHYBY vo funkciách:\n - " + "\n - ".join(errs))
    feats.sort(key=lambda p: p["order"])
    return feats


def url(p, lang):
    return f"{b.SITE}/{lang}/funkcie/{p['langs'][lang]['slug']}.html"


def shots_html(p, lang):
    L, out = p["langs"][lang], []
    alts = L.get("shots_alt") or []
    for i, img in enumerate(p.get("shots", [])[:2]):
        f = IMG / f"{img}-{lang}.webp"
        if not f.is_file():
            continue
        from PIL import Image
        w, h = Image.open(f).size
        alt = alts[i] if i < len(alts) else f"{F[lang]['shot']}: {L['name']}"
        out.append(f'<figure class="howto-shot"><img src="../../assets/navody/{f.name}" alt="{e(alt)}" '
                   f'width="{w}" height="{h}" loading="{"eager" if i == 0 else "lazy"}"></figure>')
    return (f'\n      <div class="feature-shots">{"".join(out)}</div>' if out else ""), \
        [f"{b.SITE}/assets/navody/{img}-{lang}.webp" for img in p.get("shots", [])[:2]
         if (IMG / f"{img}-{lang}.webp").is_file()]


def build_page(p, lang, by_id, guides_by_id):
    t, L = F[lang], p["langs"][lang]
    canonical = url(p, lang)
    alternates = {l: url(p, l) for l in b.LANGS}
    alt_rel = {l: f"../../{l}/funkcie/{p['langs'][l]['slug']}.html" for l in b.LANGS}
    body, _ = b.add_heading_ids(L["body"])
    shots, shot_urls = shots_html(p, lang)
    faq = L["faq"]
    article = {"@context": "https://schema.org", "@type": "Article", "headline": L["title"],
               "description": L["description"], "inLanguage": lang, "url": canonical,
               "author": {"@type": "Organization", "name": "Shoppie", "url": f"{b.SITE}/"},
               "publisher": {"@type": "Organization", "name": "Shoppie", "url": f"{b.SITE}/"},
               "about": {"@type": "MobileApplication", "name": "Shoppie", "operatingSystem": "iOS 26",
                         "applicationCategory": "LifestyleApplication",
                         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"}}}
    if p.get("updated"):
        article["dateModified"] = p["updated"]
    if shot_urls:
        article["image"] = shot_urls
    ld = [article,
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
              {"@type": "Question", "name": q["q"],
               "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", q["a"])}} for q in faq]},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": b.T[lang]["home"], "item": f"{b.SITE}/{lang}/"},
              {"@type": "ListItem", "position": 2, "name": t["h1"], "item": f"{b.SITE}/{lang}/funkcie/"},
              {"@type": "ListItem", "position": 3, "name": L["name"], "item": canonical}]}]
    extra = "".join(b.jsonld(x) for x in ld)
    items = "".join(f'\n        <details><summary>{e(q["q"])}</summary><div class="answer"><p>{q["a"]}</p></div></details>'
                    for q in faq)
    faq_html = (f'\n      <section class="post-faq" aria-labelledby="faq-h">\n        <h2 id="faq-h">{t["faq"]}</h2>'
                f'\n        <div class="card faq">{items}\n        </div>\n      </section>')
    gl = [guides_by_id[g] for g in p.get("guides", []) if g in guides_by_id]
    guides_html = ""
    if gl:
        lis = "".join(f'<li><a href="../navody/{g["langs"][lang]["slug"]}.html">{e(g["langs"][lang]["title"])}</a></li>'
                      for g in gl)
        guides_html = f'\n      <nav class="howto-related" aria-labelledby="gd-h"><h2 id="gd-h">{t["guides"]}</h2><ul>{lis}</ul></nav>'
    rel = [by_id[r] for r in p.get("related", []) if r in by_id]
    rel_html = ""
    if rel:
        lis = "".join(f'<li><a href="{r["langs"][lang]["slug"]}.html">{e(r["langs"][lang]["name"])}</a></li>'
                      for r in rel)
        rel_html = f'\n      <nav class="howto-related" aria-labelledby="rel-h"><h2 id="rel-h">{t["related"]}</h2><ul>{lis}</ul></nav>'
    upd = p.get("updated")
    meta = f'\n      <p class="meta">{t["updated"]} <time datetime="{upd}">{b.fmt_date(upd, lang)}</time></p>' if upd else ""
    return b.head(lang, f'{L["title"]} – Shoppie', L["description"], canonical, alternates, "article", extra) + \
        b.header(lang, "features", alt_rel, "../") + f"""
<main id="main" class="page post feature">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="../">{b.T[lang]['home']}</a> › <a href="./">{t['h1']}</a> › {e(L['name'])}</nav>
    <article>
      <h1>{e(L['title'])}</h1>{meta}
      <aside class="post-summary" aria-label="{t['summary']}"><h2>{t['summary']}</h2><p>{L['summary']}</p></aside>{shots}
      <div class="post-body">{body}</div>{faq_html}{guides_html}{rel_html}
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


def build_hub(feats, lang):
    t = F[lang]
    canonical = f"{b.SITE}/{lang}/funkcie/"
    alternates = {l: f"{b.SITE}/{l}/funkcie/" for l in b.LANGS}
    alt_rel = {l: f"../../{l}/funkcie/" for l in b.LANGS}
    cards = "".join(f"""
      <li><a class="card howto-card feature-card" href="{p['langs'][lang]['slug']}.html"><span class="feature-icon" aria-hidden="true"><svg class="ico"><use href="../../assets/icons.svg#{p['icon']}"/></svg></span><h2>{e(p['langs'][lang]['name'])}</h2><p>{e(p['langs'][lang]['description'])}</p><span class="post-more" aria-hidden="true">{t['more']} →</span></a></li>"""
                    for p in feats)
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": t["title"], "description": t["desc"],
           "inLanguage": lang, "url": canonical,
           "mainEntity": {"@type": "ItemList", "itemListElement": [
               {"@type": "ListItem", "position": i, "url": url(p, lang), "name": p["langs"][lang]["name"]}
               for i, p in enumerate(feats, 1)]}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": b.T[lang]["home"], "item": f"{b.SITE}/{lang}/"},
              {"@type": "ListItem", "position": 2, "name": t["h1"], "item": canonical}]}]
    return b.head(lang, t["title"], t["desc"], canonical, alternates, "website", "".join(b.jsonld(x) for x in ld)) + \
        b.header(lang, "features", alt_rel, "../") + f"""
<main id="main" class="page howto-hub feature-hub">
  <div class="wrap">
    <p class="eyebrow">{t['eyebrow']}</p>
    <h1>{t['h1']}</h1>
    <p class="lead">{t['lead']}</p>
    <ul class="howto-list feature-list">{cards}
    </ul>
  </div>
</main>
""" + b.footer(lang, "../") + "\n</body>\n</html>\n"


def build_all(guides):
    feats = load()
    if not feats:
        return [], {}
    by_id = {p["id"]: p for p in feats}
    guides_by_id = {g["id"]: g for g in guides}
    for lang in b.LANGS:
        d = b.ROOT / lang / "funkcie"
        d.mkdir(parents=True, exist_ok=True)
        keep = {"index.html"}
        for p in feats:
            name = p["langs"][lang]["slug"] + ".html"
            keep.add(name)
            (d / name).write_text(build_page(p, lang, by_id, guides_by_id), encoding="utf-8")
        for f in d.glob("*.html"):
            if f.name not in keep:
                f.unlink()
        (d / "index.html").write_text(build_hub(feats, lang), encoding="utf-8")
    groups = [{l: f"{b.SITE}/{l}/funkcie/" for l in b.LANGS}]
    groups += [{l: url(p, l) for l in b.LANGS} for p in feats]
    return groups, {url(p, l): p["updated"] for p in feats for l in b.LANGS if p.get("updated")}
