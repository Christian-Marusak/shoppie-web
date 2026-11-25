# Blog Shoppie – návod na písanie článkov

Tento návod je pre automatickú úlohu (aj pre človeka), ktorá píše články na blog
https://shoppieapp.eu/sk/blog/. Pravidlá tu sú záväzné.

## Ako blog funguje

- Každý článok je **jeden súbor** `_blog/posts/RRRR-MM-DD-<id>.json` so všetkými tromi jazykmi (sk, cs, en).
- Stránky, zoznam článkov, RSS a `sitemap.xml` vytvára skript: `python3 _blog/build.py`.
  HTML v `sk/blog/`, `cs/blog/`, `en/blog/` a `sitemap.xml` **nikdy neupravuj ručne**.
- Pred zverejnením vždy spusti kontrolu: `python3 _blog/check.py _blog/posts/<súbor>.json`.
  Ak kontrola hlási chybu, oprav ju. Ak ju nevieš opraviť, článok nezverejňuj.

## Formát súboru

```json
{
  "id": "kratky-identifikator",
  "date": "RRRR-MM-DD",
  "langs": {
    "sk": {
      "slug": "url-adresa-clanku-bez-diakritiky",
      "title": "Nadpis s hlavným kľúčovým slovom (max. 65 znakov)",
      "description": "Popis pre Google (110–160 znakov).",
      "keywords": ["hlavné kľúčové slovo", "vedľajšie", "..."],
      "summary": "2–3 vety, priama odpoveď na hlavnú otázku (max. 60 slov).",
      "body": "<p>…</p><h2>…</h2>…",
      "faq": [{"q": "Otázka?", "a": "Krátka odpoveď."}]
    },
    "cs": { … },
    "en": { … }
  }
}
```

- Voliteľne `"image"` (vytvorí ho `_blog/image.py`) a v každom jazyku `"image_alt"` – popis fotky.
- `body` je HTML. Povolené značky: `p, h2, h3, ul, ol, li, strong, em, a, table, tr, th, td, blockquote`.
  Žiadne `h1` (nadpis robí šablóna), žiadne obrázky, skripty ani štýly.
- Obsah článku a kotvy k nadpisom `h2` sa vytvoria automaticky.
- Odkaz na úvod webu: `<a href="../index.html">Shoppie</a>`. Odkaz na podporu: `../support.html`.
  Odkaz na iný článok: `iny-slug.html` (len ak ten článok existuje).
- `date` je dátum zverejnenia. Článok s budúcim dátumom sa nezobrazí, kým ten deň nepríde.

## Postup pri každom článku

1. **Prečítaj si existujúce články** v `_blog/posts/`, aby si neopakoval tému ani hlavné kľúčové slovo.
2. **Prieskum (webové vyhľadávanie):**
   - aktuálna sezóna a udalosti na Slovensku a v Česku (sviatky, ceny potravín, zľavové akcie, počasie),
   - **SEO kľúčové slová**: ako sa ľudia pýtajú v Google (návrhy pri písaní, „Ľudia sa tiež pýtajú“, súvisiace hľadania),
     pre každý jazyk zvlášť (SK, CS, EN),
   - **AIO kľúčové slová**: otázky, na ktoré odpovedajú AI prehľady v Google, ChatGPT a Perplexity.
   Vyber **jedno hlavné kľúčové slovo** na jazyk a 3–5 vedľajších.
3. **Napíš článok** v slovenčine, potom v češtine a angličtine. Nie doslovný preklad:
   každý jazyk má vlastné kľúčové slová a miestne reálie (SK: kapustnica, CS: rybí polévka, cukroví; EN: všeobecné).
4. **Vytvor súbor** článku.
5. **Fotka k článku** (ak je nastavená premenná `GEMINI_API_KEY`):
   - do každého jazyka doplň `image_alt` – stručný popis toho, čo je na fotke (max. 200 znakov),
   - spusti `python3 _blog/image.py _blog/posts/<súbor>.json "<popis scény po anglicky>"`.
     Popis opisuje fotku k téme článku (napr. potraviny, kuchyňa, nákup, špajza), stredoeurópske prostredie.
     Pravidlá „bez textu, log, ľudí a telefónov“ pridá skript sám.
   - Pozri si vytvorenú fotku (`assets/blog/<id>.webp`). Ak je na nej text, logo, človek, telefón, alebo nesedí
     k téme či k `image_alt`, spusti skript znova (najviac 2-krát) alebo uprav `image_alt` podľa skutočnej fotky.
   - Ak kľúč chýba (kód 2) alebo Gemini zlyhá, pokračuj bez fotky a napíš to v záverečnej správe.
6. Spusti `python3 _blog/check.py …` a `python3 _blog/build.py`.
7. Ďalší postup (schválenie alebo zverejnenie) určuje zadanie úlohy.

## Témy (striedaj ich)

1. Tipy na nákup a šetrenie (plánovanie, zľavy, rozpočet domácnosti, porovnávanie cien).
2. Spotreba a menej vyhadzovania jedla (skladovanie, dátumy spotreby, mrazenie, zvyšky).
3. Sezónne zoznamy (sviatky, grilovanie, návrat do školy, Veľká noc, chata). Píš ich **2–3 týždne vopred**.
4. Návody na Shoppie (ako využiť funkciu na konkrétnu situáciu). Najviac **1 z 3 článkov**.

## Štýl

- Dĺžka **600–900 slov** na jazyk (vrátane zhrnutia a FAQ).
- **Vykanie** v SK aj CS („skontrolujte“, „vaše zásoby“), o nás v množnom čísle („pripravili sme“).
  Nikdy tykanie. V angličtine prirodzené „you“.
- Na začiatku `summary`: krátka, priama odpoveď (tú citujú AI prehľady). Potom úvodný odsek, 4–7 nadpisov `h2`,
  odrážky alebo tabuľka tam, kde pomôžu, a **3–5 otázok vo FAQ** (formulované tak, ako sa ľudia pýtajú).
- Hlavné kľúčové slovo v nadpise, v popise, v zhrnutí a v prvom odseku. Prirodzene, žiadne „vypchávanie“.
- Konkrétne a užitočné rady. Žiadne vymyslené štatistiky. Ak uvádzaš číslo alebo fakt, musí byť z dôveryhodného
  zdroja a pridaj naň odkaz.
- Shoppie spomeň prirodzene, najčastejšie v poslednej časti. Článok nesmie byť reklama.

## Čo Shoppie naozaj vie (spomínaj LEN toto)

- Nákupný zoznam pre iPhone s iOS 26, zadarmo, bez reklám, bez registrácie.
- Rýchle pridávanie: asi 540 bežných produktov, sám ich zaradí do kategórie, pridáte aj množstvo.
- Koliesko obľúbených (podržanie +), obsah si nastavíte sami.
- Návrhy: učí sa z vašich nákupov a navrhne, čo asi dochádza.
- Viac zoznamov (napr. samostatný zoznam „Vianoce“).
- Dokončenie nákupu → História (obchod, počet položiek), potiahnutím doprava položku znova pridáte.
- Sken bločku: rozpozná produkty aj ceny vrátane zliav, priamo v iPhone, aj offline.
- Spotreba: kúpené potraviny sa objavia samy s odhadovaným dátumom spotreby (dá sa upraviť); ráno pripomenie,
  čo treba zjesť; potraviny po dátume môže automaticky odstrániť (vypnuté v predvolenom stave).
- Pravidelné položky: v zvolený deň sa pridajú do zoznamu samy.
- Záruky aj s fotkou bločku a pripomienkou pred koncom.
- Spoločná domácnosť cez iCloud: členovia vidia zoznamy, históriu, Spotrebu a pravidelné položky, zmeny hneď.
- Slovenčina, čeština, angličtina; tmavý režim; VoiceOver a veľké písmo; režim na šírku; iPhone Duo.
- Súkromie: nič nezbiera, žiadne účty ani server, všetko je v iPhone a v súkromnom iCloude.

**Nikdy netvrď**, že Shoppie má: widget, poznámky k položkám, prehľad/štatistiky výdavkov, rozpočet, ceny vopred,
režim v obchode, zamknutú obrazovku, Apple Watch, Android, web, Mac, export, zdieľanie cez odkaz, účet či prihlásenie.
Niektoré z týchto vecí sú v pláne („Čo chystáme“), ale **nesľubuj ich ani nespomínaj ako hotové**.

## Odkaz na App Store

Šablóna pridá na koniec článku kartu „Vyskúšajte Shoppie“ s odznakom App Store sama. Do textu ho nepridávaj.
