#!/usr/bin/env python3
"""Kontrola článku pred zverejnením.

Použitie:  python3 _blog/check.py _blog/posts/<subor>.json
Výsledok:  "OK" a kód 0, alebo zoznam CHÝB a kód 1.
Pravidlá sú v _blog/README.md.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_blog" / "posts"
LANGS = ("sk", "cs", "en")
ALLOWED_TAGS = {"p", "h2", "h3", "ul", "ol", "li", "strong", "em", "a", "table", "tr", "th", "td", "blockquote", "br"}

# Tykanie (2. osoba jednotného čísla) – časté tvary
TYKANIE = {
    "sk": r"\b(tvoj\w*|tvoj|tebe|teba|tebou|máš|môžeš|chceš|potrebuješ|vieš|budeš|urob|skús|nezabudni|pridaj|kúp|ulož|"
          r"skontroluj|napíš|pozri|vyskúšaj|stiahni|otvor|zapni|vypni|zisti|nakupuj|plánuj|zamraz)\b",
    "cs": r"\b(tvůj|tvoje|tvého|tvému|tvých|tebe|tebou|máš|můžeš|chceš|potřebuješ|víš|budeš|udělej|zkus|nezapomeň|"
          r"přidej|kup|ulož|zkontroluj|napiš|podívej|vyzkoušej|stáhni|otevři|zapni|vypni|zjisti|nakupuj|plánuj|zamraz)\b",
}
# Funkcie, ktoré Shoppie NEMÁ – nesmú sa spomínať v súvislosti s aplikáciou
NOT_FEATURES = r"(widget|poznámk|poznámek|note[s]? to|item notes|rozpočet|rozpočt|budget|zamknut|zamčen|lock screen|" \
               r"apple watch|android|export|mac\b|webov[áa] verzi|web version|prihlás|přihláš|sign in|log in|účet|account)"
APP_WORDS = r"(shoppie|aplikáci|aplikaci|the app\b|in the app)"


def text(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def check(path):
    errors = []
    p = json.loads(Path(path).read_text(encoding="utf-8"))
    for k in ("id", "date", "langs"):
        if k not in p:
            errors.append(f"chýba pole '{k}'")
    if errors:
        return errors
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", p["date"]):
        errors.append("date musí byť RRRR-MM-DD")
    others = {}
    for f in POSTS.glob("*.json"):
        if f.resolve() != Path(path).resolve():
            o = json.loads(f.read_text(encoding="utf-8"))
            others[o["id"]] = o
    img = p.get("image")
    if img:
        for k in ("file", "thumb", "share"):
            if not (ROOT / img.get(k, "")).is_file():
                errors.append(f"obrázok '{img.get(k)}' neexistuje")
        for l in LANGS:
            alt = p["langs"].get(l, {}).get("image_alt", "")
            if not alt or len(alt) > 200:
                errors.append(f"[{l}] image_alt chýba alebo je dlhší ako 200 znakov")
    if p["id"] in others:
        errors.append(f"id '{p['id']}' už existuje")
    for l in LANGS:
        L = p["langs"].get(l)
        if not L:
            errors.append(f"[{l}] chýba jazyk")
            continue
        missing = [k for k in ("slug", "title", "description", "keywords", "summary", "body", "faq") if not L.get(k)]
        if missing:
            errors.extend(f"[{l}] chýba '{k}'" for k in missing)
            continue
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", L["slug"]):
            errors.append(f"[{l}] slug: len malé písmená bez diakritiky, čísla a pomlčky")
        for o in others.values():
            if o["langs"][l]["slug"] == L["slug"]:
                errors.append(f"[{l}] slug '{L['slug']}' už používa článok '{o['id']}'")
        if len(L["title"]) > 65:
            errors.append(f"[{l}] nadpis má {len(L['title'])} znakov (max. 65)")
        if not 110 <= len(L["description"]) <= 160:
            errors.append(f"[{l}] popis má {len(L['description'])} znakov (110–160)")
        sw = len(text(L["summary"]).split())
        if sw > 60:
            errors.append(f"[{l}] zhrnutie má {sw} slov (max. 60)")
        if not 3 <= len(L["faq"]) <= 5:
            errors.append(f"[{l}] FAQ má {len(L['faq'])} otázok (3–5)")
        full = " ".join([L["summary"], L["body"]] + [q["q"] + " " + q["a"] for q in L["faq"]])
        words = len(text(full).split())
        if not 550 <= words <= 1000:
            errors.append(f"[{l}] dĺžka {words} slov (cieľ 600–900)")
        tags = {t.lower() for t in re.findall(r"</?([a-zA-Z0-9]+)", L["body"])}
        bad = tags - ALLOWED_TAGS
        if bad:
            errors.append(f"[{l}] nepovolené HTML značky: {', '.join(sorted(bad))}")
        if re.search(r'href="[^"]*index\.html', L["body"]):
            errors.append(f"[{l}] odkaz na …/index.html – použite čistú adresu (napr. ../ alebo ../navody/)")
        if L["body"].count("<h2") < 3:
            errors.append(f"[{l}] článok má menej ako 3 nadpisy h2")
        main_kw = L["keywords"][0].lower()
        if main_kw not in (L["title"] + " " + L["description"] + " " + L["summary"]).lower():
            errors.append(f"[{l}] hlavné kľúčové slovo '{main_kw}' nie je v nadpise, popise ani zhrnutí")
        if l in TYKANIE:
            hits = sorted({m.group(0) for m in re.finditer(TYKANIE[l], text(full), re.I)})
            if hits:
                errors.append(f"[{l}] možné tykanie: {', '.join(hits)}")
        for sent in re.split(r"(?<=[.!?])\s+", text(full)):
            if re.search(APP_WORDS, sent, re.I) and re.search(NOT_FEATURES, sent, re.I):
                errors.append(f"[{l}] veta spomína funkciu, ktorú Shoppie nemá: „{sent[:120]}“")
        for href in re.findall(r'href="([^"]+)"', L["body"]):
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = (ROOT / l / "blog" / href).resolve()
            slugs = {o["langs"][l]["slug"] + ".html" for o in others.values()}
            if not target.exists() and Path(href).name not in slugs:
                errors.append(f"[{l}] neplatný odkaz: {href}")
    errors += check_social(p)
    return errors


def check_social(p):
    """Príspevok na Facebook a Instagram (pole "social", nepovinné)."""
    s = p.get("social")
    if s is None:
        return []
    errors = []
    for k in ("headline", "subline", "image", "fb", "ig"):
        if not isinstance(s.get(k), str) or not s.get(k).strip():
            errors.append(f"[social] chýba pole '{k}'")
    if errors:
        return errors
    if not (ROOT / s["image"]).exists():
        errors.append(f"[social] obrázok '{s['image']}' neexistuje")
    url = f"https://shoppieapp.eu/sk/blog/{p['langs']['sk']['slug']}.html"
    if url not in s["fb"]:
        errors.append(f"[social] fb musí obsahovať odkaz {url}")
    if "Odkaz nájdete v profile" not in s["ig"] or "http" in s["ig"]:
        errors.append("[social] ig musí mať „Odkaz nájdete v profile 🔗“ a žiadny odkaz")
    for k in ("fb", "ig"):
        t = s[k]
        if len(t) > 900:
            errors.append(f"[social] {k} má {len(t)} znakov (max. 900)")
        if re.search(r"<[a-z/][^>]*>", t):
            errors.append(f"[social] {k} obsahuje HTML")
        if "#shoppie" not in t:
            errors.append(f"[social] {k} nemá hashtag #shoppie")
        hits = sorted({m.group(0) for m in re.finditer(TYKANIE["sk"], t, re.I)})
        if hits:
            errors.append(f"[social] {k} – možné tykanie: {', '.join(hits)}")
        for sent in re.split(r"(?<=[.!?\n])\s+", t):
            if re.search(APP_WORDS, sent, re.I) and re.search(NOT_FEATURES, sent, re.I):
                errors.append(f"[social] {k} spomína funkciu, ktorú Shoppie nemá: „{sent[:100]}“")
    return errors


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    errs = check(sys.argv[1])
    if errs:
        print("CHYBY:")
        for e in errs:
            print(" -", e)
        sys.exit(1)
    print("OK")
