#!/usr/bin/env python3
"""Generátor blogu Shoppie.

Každý článok je jeden súbor _blog/posts/<id>.json so všetkými tromi jazykmi.
Spustenie (z koreňa repozitára):  python3 _blog/build.py

Skript vytvorí/prepíše:
  {sk,cs,en}/blog/index.html      – zoznam článkov
  {sk,cs,en}/blog/<slug>.html     – jednotlivé články
  {sk,cs,en}/blog/feed.xml        – RSS
  sitemap.xml                     – mapa celého webu
Návod pre písanie článkov: _blog/README.md
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_blog" / "posts"
SITE = "https://shoppieapp.eu"
LANGS = ("sk", "cs", "en")
AUTHOR = "Christián Marušák"
EMAIL = "christianm@outlook.sk"

STORE = {
    "sk": "https://apps.apple.com/sk/app/id6832107172?l=sk",
    "cs": "https://apps.apple.com/cz/app/id6832107172?l=cs",
    "en": "https://apps.apple.com/sk/app/id6832107172",
}
MONTHS = {
    "sk": ["januára", "februára", "marca", "apríla", "mája", "júna", "júla", "augusta",
           "septembra", "októbra", "novembra", "decembra"],
    "cs": ["ledna", "února", "března", "dubna", "května", "června", "července", "srpna",
           "září", "října", "listopadu", "prosince"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
}
T = {
    "sk": dict(
        locale="sk_SK", skip="Preskočiť na obsah", menu="Hlavné menu", lang_label="Jazyk",
        home="Úvod", roadmap="Čo chystáme", blog="Blog", support="Podpora", privacy="Súkromie",
        blog_title="Blog – Shoppie",
        blog_desc="Tipy na nákupy, šetrenie a menej vyhadzovania jedla od tvorcov aplikácie Shoppie.",
        blog_lead="Tipy na nákupy, šetrenie a menej vyhadzovania jedla. Pravidelne nové články.",
        empty="Prvé články pripravujeme. Čoskoro tu budú.",
        read="min čítania", published="Publikované", updated="Aktualizované",
        summary="Stručne", toc="Obsah článku", faq="Časté otázky", back="Späť na blog",
        read_more="Čítať článok",
        cta_h="Vyskúšajte Shoppie",
        cta_p="Nákupný zoznam pre iPhone, ktorý sa učí. Zadarmo, bez reklám a bez registrácie.",
        badge_alt="Stiahnuť v App Store", rss="RSS kanál blogu Shoppie",
        og_alt="Shoppie – nákupný zoznam pre iPhone, ukážky aplikácie",
        names={"sk": "Slovenčina", "cs": "Čeština", "en": "English"},
    ),
    "cs": dict(
        locale="cs_CZ", skip="Přeskočit na obsah", menu="Hlavní menu", lang_label="Jazyk",
        home="Úvod", roadmap="Co chystáme", blog="Blog", support="Podpora", privacy="Soukromí",
        blog_title="Blog – Shoppie",
        blog_desc="Tipy na nákupy, šetření a méně vyhazování jídla od tvůrců aplikace Shoppie.",
        blog_lead="Tipy na nákupy, šetření a méně vyhazování jídla. Pravidelně nové články.",
        empty="První články připravujeme. Brzy tu budou.",
        read="min čtení", published="Publikováno", updated="Aktualizováno",
        summary="Stručně", toc="Obsah článku", faq="Časté otázky", back="Zpět na blog",
        read_more="Číst článek",
        cta_h="Vyzkoušejte Shoppie",
        cta_p="Nákupní seznam pro iPhone, který se učí. Zdarma, bez reklam a bez registrace.",
        badge_alt="Stáhnout v App Store", rss="RSS kanál blogu Shoppie",
        og_alt="Shoppie – nákupní seznam pro iPhone, ukázky aplikace",
        names={"sk": "Slovenčina", "cs": "Čeština", "en": "English"},
    ),
    "en": dict(
        locale="en_GB", skip="Skip to content", menu="Main menu", lang_label="Language",
        home="Home", roadmap="What’s coming", blog="Blog", support="Support", privacy="Privacy",
        blog_title="Blog – Shoppie",
        blog_desc="Tips on grocery shopping, saving money and wasting less food from the makers of Shoppie.",
        blog_lead="Tips on grocery shopping, saving money and wasting less food. New articles regularly.",
        empty="Our first articles are on the way.",
        read="min read", published="Published", updated="Updated",
        summary="In short", toc="Contents", faq="Frequently asked questions", back="Back to the blog",
        read_more="Read the article",
        cta_h="Try Shoppie",
        cta_p="The iPhone shopping list that learns. Free, no ads and no sign-up.",
        badge_alt="Download on the App Store", rss="Shoppie blog RSS feed",
        og_alt="Shoppie – shopping list for iPhone, app screenshots",
        names={"sk": "Slovenčina", "cs": "Čeština", "en": "English"},
    ),
}

e = html.escape
CUR_PAGE = ' aria-current="page"'
CUR_TRUE = ' aria-current="true"'


def fmt_date(d, lang):
    y, m, dd = (int(x) for x in d.split("-"))
    if lang == "en":
        return f"{dd} {MONTHS['en'][m - 1]} {y}"
    return f"{dd}. {MONTHS[lang][m - 1]} {y}"


def slugify(text):
    s = text.lower()
    table = str.maketrans("áäčďéěíĺľňóôŕřšťúůýž", "aacdeeillnoorrstuuyz")
    s = s.translate(table)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "sekcia"


def words(text):
    return len(re.sub(r"<[^>]+>", " ", text).split())


def load_posts():
    posts = []
    for f in sorted(POSTS.glob("*.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        p["_file"] = f.name
        for k in ("id", "date", "langs"):
            if k not in p:
                sys.exit(f"{f.name}: chýba pole '{k}'")
        for l in LANGS:
            L = p["langs"].get(l)
            if not L:
                sys.exit(f"{f.name}: chýba jazyk '{l}'")
            for k in ("slug", "title", "description", "summary", "body"):
                if not L.get(k):
                    sys.exit(f"{f.name}/{l}: chýba pole '{k}'")
            if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", L["slug"]):
                sys.exit(f"{f.name}/{l}: slug smie mať len malé písmená bez diakritiky, čísla a pomlčky")
        if p["date"] > date.today().isoformat() and not p.get("draft"):
            pass  # článok s budúcim dátumom sa zverejní, až keď príde jeho deň
        posts.append(p)
    posts.sort(key=lambda p: (p["date"], p["id"]), reverse=True)
    return posts


def visible(posts):
    today = date.today().isoformat()
    return [p for p in posts if not p.get("draft") and p["date"] <= today]


def add_heading_ids(body):
    seen = set()
    toc = []

    def rep(m):
        attrs, inner = m.group(1), m.group(2)
        text = re.sub(r"<[^>]+>", "", inner)
        if "id=" in attrs:
            hid = re.search(r'id="([^"]+)"', attrs).group(1)
        else:
            hid = slugify(text)
            base, n = hid, 2
            while hid in seen:
                hid, n = f"{base}-{n}", n + 1
            attrs = f'{attrs} id="{hid}"'
        seen.add(hid)
        toc.append((hid, text))
        return f"<h2{attrs}>{inner}</h2>"

    body = re.sub(r"<h2([^>]*)>(.*?)</h2>", rep, body, flags=re.S)
    return body, toc


def header(lang, current, alt_links, up):
    t = T[lang]
    items = [
        (f"{up}index.html", t["home"], current == "home"),
        (f"{up}index.html#roadmap", t["roadmap"], False),
        (f"{up}blog/index.html", t["blog"], current == "blog"),
        (f"{up}support.html", t["support"], False),
        (f"{up}privacy.html", t["privacy"], False),
    ]
    nav = "".join(
        f'<a href="{h}"{CUR_PAGE if cur else ""}>{e(lbl)}</a>' for h, lbl, cur in items
    )
    langs = "".join(
        f'<li><a href="{alt_links[l]}" hreflang="{l}" lang="{l}" title="{t["names"][l]}"'
        f'{CUR_TRUE if l == lang else ""}><span aria-hidden="true">{l.upper()}</span>'
        f'<span class="sr-only">{t["names"][l]}</span></a></li>'
        for l in LANGS
    )
    a = "../" + up
    return f"""<a class="skip" href="#main">{t['skip']}</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{up}index.html"><img src="{a}assets/logo.svg" data-xmas="{a}assets/img/xmas/icon-christmas.png" alt="" width="32" height="32"><span>Shoppie</span></a>
    <nav class="main-nav" aria-label="{t['menu']}">{nav}</nav>
    <div class="header-end">
      <nav aria-label="{t['lang_label']}">
        <ul class="lang">
          {langs}
        </ul>
      </nav>
      <details class="menu-toggle">
        <summary aria-label="Menu"><span class="burger" aria-hidden="true"></span></summary>
        <nav class="menu-panel" aria-label="{t['menu']}" onclick="this.parentNode.open = false">{nav}</nav>
      </details>
    </div>
  </div>
</header>"""


def footer(lang, up):
    t = T[lang]
    return f"""<footer class="site-footer">
  <div class="wrap">
    <nav aria-label="Shoppie">
      <a href="{up}blog/index.html">{t['blog']}</a> ·
      <a href="{up}support.html">{t['support']}</a> ·
      <a href="{up}privacy.html">{t['privacy']}</a> ·
      <a href="mailto:{EMAIL}">{EMAIL}</a>
    </nav>
    <p>© {date.today().year} {AUTHOR}</p>
  </div>
</footer>"""


def head(lang, title, desc, canonical, alternates, og_type, extra="", up="../", og=None):
    t = T[lang]
    a = "../" + up
    alts = "\n".join(f'  <link rel="alternate" hreflang="{l}" href="{u}">' for l, u in alternates.items())
    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}">
  <meta name="author" content="{AUTHOR}">
  <meta name="color-scheme" content="light dark">
  <meta name="theme-color" content="#F2F2F7" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="{og_type}">
  <meta property="og:site_name" content="Shoppie">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(desc)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{og['url'] if og else f'{SITE}/assets/og-{lang}.png'}">
  <meta property="og:image:width" content="{og['w'] if og else 1200}">
  <meta property="og:image:height" content="{og['h'] if og else 630}">
  <meta property="og:image:alt" content="{e(og['alt'] if og else t['og_alt'])}">
  <meta name="twitter:card" content="summary_large_image">
  <meta property="og:locale" content="{t['locale']}">
  <meta name="apple-itunes-app" content="app-id=6832107172">
  <link rel="icon" href="{a}favicon.svg" type="image/svg+xml">
  <link rel="icon" href="{a}favicon-32.png" sizes="32x32" type="image/png">
  <link rel="apple-touch-icon" href="{a}apple-touch-icon.png">
{alts}
  <link rel="alternate" hreflang="x-default" href="{alternates['sk']}">
  <link rel="alternate" type="application/rss+xml" title="{e(t['rss'])}" href="{SITE}/{lang}/blog/feed.xml">
  <link rel="stylesheet" href="{a}assets/style.css">
  <script src="{a}assets/xmas.js"></script>
{extra}</head>
<body>
"""


def jsonld(obj):
    s = json.dumps(obj, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f'  <script type="application/ld+json">\n{s}\n  </script>\n'


def badge(lang, a):
    return (f'<a class="store-badge" href="{STORE[lang]}"><img src="{a}assets/badges/app-store-{lang}.svg" '
            f'alt="{T[lang]["badge_alt"]}" width="162" height="54"></a>')


def post_url(p, lang):
    return f"{SITE}/{lang}/blog/{p['langs'][lang]['slug']}.html"


def build_article(p, lang):
    t = T[lang]
    L = p["langs"][lang]
    body, toc = add_heading_ids(L["body"])
    faq = L.get("faq") or []
    total_words = words(L["summary"]) + words(body) + sum(words(q["q"]) + words(q["a"]) for q in faq)
    minutes = max(1, round(total_words / 200))
    canonical = post_url(p, lang)
    alternates = {l: post_url(p, l) for l in LANGS}
    updated = p.get("updated")
    ld = [{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": L["title"],
        "description": L["description"],
        "inLanguage": lang,
        "datePublished": p["date"],
        "dateModified": updated or p["date"],
        "author": {"@type": "Person", "name": AUTHOR},
        "publisher": {"@type": "Organization", "name": "Shoppie",
                      "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/icon-512.png"}},
        "image": f"{SITE}/{p['image'].get('share') or p['image']['file']}" if p.get("image") else f"{SITE}/assets/og-{lang}.png",
        "mainEntityOfPage": canonical,
        "keywords": ", ".join(L.get("keywords", [])),
        "wordCount": total_words,
    }, {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": t["home"], "item": f"{SITE}/{lang}/"},
            {"@type": "ListItem", "position": 2, "name": t["blog"], "item": f"{SITE}/{lang}/blog/"},
            {"@type": "ListItem", "position": 3, "name": L["title"], "item": canonical},
        ],
    }]
    if faq:
        ld.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q["q"],
                            "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", q["a"])}}
                           for q in faq],
        })
    extra = "".join(jsonld(x) for x in ld)
    if p.get("draft"):
        extra += '  <meta name="robots" content="noindex">\n'
    alt_rel = {l: f"../../{l}/blog/{p['langs'][l]['slug']}.html" for l in LANGS}
    toc_html = ""
    if len(toc) >= 3:
        lis = "".join(f'<li><a href="#{hid}">{e(txt)}</a></li>' for hid, txt in toc)
        toc_html = f'\n      <nav class="post-toc" aria-label="{t["toc"]}"><h2>{t["toc"]}</h2><ol>{lis}</ol></nav>'
    faq_html = ""
    if faq:
        items = "".join(
            f'\n        <details><summary>{e(q["q"])}</summary><div class="answer"><p>{q["a"]}</p></div></details>'
            for q in faq)
        faq_html = f'\n      <section class="post-faq" aria-labelledby="faq-h">\n        <h2 id="faq-h">{t["faq"]}</h2>\n        <div class="card faq">{items}\n        </div>\n      </section>'
    img = p.get("image")
    og = hero = None
    if img:
        alt = L.get("image_alt", "")
        og = {"url": f"{SITE}/{img.get('share') or img['file']}", "w": img["width"], "h": img["height"], "alt": alt}
        hero = (f'\n      <figure class="post-hero"><img src="../../{img["file"]}" alt="{e(alt)}" '
                f'width="{img["width"]}" height="{img["height"]}" fetchpriority="high"></figure>')
    upd = (f' · {t["updated"]} <time datetime="{updated}">{fmt_date(updated, lang)}</time>' if updated else "")
    return head(lang, f'{L["title"]} – Shoppie', L["description"], canonical, alternates, "article", extra, og=og) + \
        header(lang, "blog", alt_rel, "../") + f"""
<main id="main" class="page post">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="../index.html">{t['home']}</a> › <a href="index.html">{t['blog']}</a></nav>
    <article>
      <h1>{e(L['title'])}</h1>
      <p class="meta">{t['published']} <time datetime="{p['date']}">{fmt_date(p['date'], lang)}</time>{upd} · {minutes} {t['read']}</p>{hero or ""}
      <aside class="post-summary" aria-label="{t['summary']}"><h2>{t['summary']}</h2><p>{L['summary']}</p></aside>{toc_html}
      <div class="post-body">
{body}
      </div>{faq_html}
      <aside class="post-cta">
        <img src="../../assets/logo.svg" data-xmas="../../assets/img/xmas/icon-christmas.png" alt="" width="64" height="64">
        <div><h2>{t['cta_h']}</h2><p>{t['cta_p']}</p></div>
        {badge(lang, '../../')}
      </aside>
    </article>
    <p class="post-back"><a href="index.html">← {t['back']}</a></p>
  </div>
</main>
""" + footer(lang, "../") + "\n</body>\n</html>\n"


def thumb(p):
    img = p.get("image")
    if not img:
        return ""
    src = img.get("thumb") or img["file"]
    w, h = (640, round(640 * img["height"] / img["width"])) if img.get("thumb") else (img["width"], img["height"])
    return f'\n          <img class="post-thumb" src="../../{src}" alt="" width="{w}" height="{h}" loading="lazy">'


def build_index(posts, lang):
    t = T[lang]
    canonical = f"{SITE}/{lang}/blog/"
    alternates = {l: f"{SITE}/{l}/blog/" for l in LANGS}
    alt_rel = {l: f"../../{l}/blog/index.html" for l in LANGS}
    cards = "".join(
        f"""<li class="card post-card">{thumb(p)}
          <p class="meta"><time datetime="{p['date']}">{fmt_date(p['date'], lang)}</time></p>
          <h2><a href="{p['langs'][lang]['slug']}.html">{e(p['langs'][lang]['title'])}</a></h2>
          <p>{e(p['langs'][lang]['description'])}</p>
          <span class="post-more" aria-hidden="true">{t['read_more']} →</span>
        </li>""" for p in posts)
    ld = jsonld({
        "@context": "https://schema.org", "@type": "Blog", "name": t["blog_title"],
        "description": t["blog_desc"], "inLanguage": lang, "url": canonical,
        "blogPost": [{"@type": "BlogPosting", "headline": p["langs"][lang]["title"],
                      "datePublished": p["date"], "url": post_url(p, lang)} for p in posts],
    })
    return head(lang, t["blog_title"], t["blog_desc"], canonical, alternates, "website", ld) + \
        header(lang, "blog", alt_rel, "../") + f"""
<main id="main" class="page blog">
  <div class="wrap">
    <h1>{t['blog']}</h1>
    <p class="lead">{t['blog_lead']}</p>
    <ul class="post-list">{cards}</ul>
    <p class="post-empty">{t['empty']}</p>
  </div>
</main>
""" + footer(lang, "../") + "\n</body>\n</html>\n"


def rfc822(d):
    from email.utils import format_datetime
    from datetime import datetime, timezone
    y, m, dd = (int(x) for x in d.split("-"))
    return format_datetime(datetime(y, m, dd, 8, 0, tzinfo=timezone.utc))


def build_feed(posts, lang):
    t = T[lang]
    items = "".join(f"""
    <item>
      <title>{e(p['langs'][lang]['title'])}</title>
      <link>{post_url(p, lang)}</link>
      <guid isPermaLink="true">{post_url(p, lang)}</guid>
      <pubDate>{rfc822(p['date'])}</pubDate>
      <description>{e(p['langs'][lang]['description'])}</description>
    </item>""" for p in posts[:30])
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{e(t['blog_title'])}</title>
    <link>{SITE}/{lang}/blog/</link>
    <description>{e(t['blog_desc'])}</description>
    <language>{lang}</language>
    <atom:link href="{SITE}/{lang}/blog/feed.xml" rel="self" type="application/rss+xml"/>{items}
  </channel>
</rss>
"""


def build_sitemap(posts):
    groups = [{l: f"{SITE}/{l}/" for l in LANGS}]
    for page in ("support", "privacy"):
        groups.append({l: f"{SITE}/{l}/{page}.html" for l in LANGS})
    groups.append({l: f"{SITE}/{l}/blog/" for l in LANGS})
    lastmod = {}
    for p in posts:
        g = {l: post_url(p, l) for l in LANGS}
        groups.append(g)
        for u in g.values():
            lastmod[u] = p.get("updated") or p["date"]
    out = []
    for g in groups:
        alts = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{u}"/>' for l, u in g.items())
        xd = f"{SITE}/" if g["sk"] == f"{SITE}/sk/" else g["sk"]
        alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{xd}"/>'
        for u in g.values():
            lm = f"\n    <lastmod>{lastmod[u]}</lastmod>" if u in lastmod else ""
            out.append(f"  <url>\n    <loc>{u}</loc>{lm}{alts}\n  </url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(out) + "\n</urlset>\n")


def main():
    posts = load_posts()
    pub = visible(posts)
    for lang in LANGS:
        d = ROOT / lang / "blog"
        d.mkdir(parents=True, exist_ok=True)
        keep = {"index.html", "feed.xml"}
        for p in posts:
            if p in pub or p.get("draft"):
                keep.add(p["langs"][lang]["slug"] + ".html")
        for p in posts:
            if p in pub or p.get("draft"):
                (d / f"{p['langs'][lang]['slug']}.html").write_text(build_article(p, lang), encoding="utf-8")
        # odstráni stránky článkov, ktoré už nemajú zdrojový súbor
        for f in d.glob("*.html"):
            if f.name not in keep:
                f.unlink()
        (d / "index.html").write_text(build_index(pub, lang), encoding="utf-8")
        (d / "feed.xml").write_text(build_feed(pub, lang), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(build_sitemap(pub), encoding="utf-8")
    drafts = [p["id"] for p in posts if p.get("draft")]
    print(f"Hotovo: {len(pub)} zverejnených článkov" + (f", koncepty: {', '.join(drafts)}" if drafts else ""))


if __name__ == "__main__":
    main()
