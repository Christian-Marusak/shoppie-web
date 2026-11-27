#!/usr/bin/env python3
"""Vytvorí obrázok na Facebook a Instagram k článku (Gemini, 4:5, 1080 × 1350, slovenský nadpis v obrázku).

Použitie:
  python3 _blog/social.py _blog/posts/<subor>.json "<scéna v angličtine>" "<nadpis SK>" "<podnadpis SK>"

Potrebuje GEMINI_API_KEY (kľúč nikdy nepatrí do repozitára). Bez kľúča skončí kódom 2.
Výsledok: assets/social/<id>.jpg a v JSON článku pole "social" (headline, subline, image).
Texty príspevkov (social.fb, social.ig) dopĺňa autor článku podľa _blog/README.md.
Po vytvorení si obrázok VŽDY pozri a nadpis skontroluj písmeno po písmene (diakritika);
ak je chybný, spusti skript znova (najviac 3 pokusy).
"""
import base64
import io
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
SUFFIX = (
    ' In the upper part of the image, on a calm darker area, place a headline in a clean bold white sans-serif font,'
    ' exactly: "{h}", and below it in smaller white text, exactly: "{s}". Spell the Slovak text exactly, character by'
    " character, including all diacritics. No other text anywhere: no labels, no printed words on packaging, no numbers."
    " No people, no faces, no hands, no phones or screens, no logos or brand names."
    " Vertical 4:5 Instagram post, photorealistic editorial photography, soft natural light, fresh green accents."
)


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    post_path, scene, headline, subline = sys.argv[1:]
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("GEMINI_API_KEY chýba – obrázok na sociálne siete sa nevytvorí.")
        sys.exit(2)
    post_file = Path(post_path)
    post = json.loads(post_file.read_text(encoding="utf-8"))
    body = {
        "contents": [{"parts": [{"text": scene + SUFFIX.format(h=headline, s=subline)}]}],
        "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "4:5"}},
    }
    r = subprocess.run(
        ["curl", "-s", "--http1.1", "-X", "POST",
         f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
         "-H", "x-goog-api-key: " + key, "-H", "Content-Type: application/json", "--data-binary", "@-"],
        input=json.dumps(body), capture_output=True, text=True,
    )
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        sys.exit("Neplatná odpoveď od Gemini.")
    if "error" in d:
        sys.exit("Chyba Gemini: " + d["error"].get("message", "")[:300])
    data = next((p["inlineData"]["data"] for c in d.get("candidates", [])
                 for p in c.get("content", {}).get("parts", []) if "inlineData" in p), None)
    if not data:
        sys.exit("Gemini nevrátil obrázok.")
    out = ROOT / "assets" / "social" / f"{post['id']}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(io.BytesIO(base64.b64decode(data))).convert("RGB")
    ImageOps.fit(im, (1080, 1350), Image.LANCZOS).save(out, "JPEG", quality=88)
    social = post.get("social", {})
    social.update({"headline": headline, "subline": subline, "image": f"assets/social/{post['id']}.jpg"})
    post["social"] = social
    post_file.write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ok", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
