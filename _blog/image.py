#!/usr/bin/env python3
"""Vytvorí fotku k článku cez Gemini a zapíše ju do súboru článku.

Použitie:
  python3 _blog/image.py _blog/posts/<subor>.json "<popis fotky v angličtine>"

Potrebuje premennú prostredia GEMINI_API_KEY (kľúč nikdy nepatrí do repozitára).
Ak kľúč chýba, skript skončí kódom 2 a článok ostane bez fotky – to je v poriadku.

Výsledok:
  assets/blog/<id>.webp      – veľká fotka (článok, zdieľanie, Google)
  assets/blog/<id>-640.webp  – náhľad do zoznamu článkov
  assets/blog/<id>.jpg       – obrázok pri zdieľaní na sociálnych sieťach
  a v JSON článku pole "image". Popis fotky pre nevidiacich patrí do langs.<jazyk>.image_alt.
"""
import base64
import io
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
RULES = (
    " Style: photorealistic, natural editorial food and home photography, soft natural light, calm composition,"
    " colour palette with fresh or deep green accents that fits a grocery-list app."
    " Strictly no text anywhere: no words, letters, numbers, labels or printed packaging – use plain unmarked"
    " bags, jars and paper. No logos or brand names. No people, no faces, no hands. No phones, tablets or screens."
    " Wide 16:9 landscape photo."
)


def generate(prompt):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("GEMINI_API_KEY chýba – fotka sa nevytvorí.")
        sys.exit(2)
    body = {"contents": [{"parts": [{"text": prompt + RULES}]}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9"}}}
    r = subprocess.run(
        ["curl", "-s", "--http1.1", "-X", "POST",
         f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
         "-H", "x-goog-api-key: " + key, "-H", "Content-Type: application/json", "-d", json.dumps(body)],
        capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        sys.exit(f"Gemini nevrátil platnú odpoveď (curl kód {r.returncode}).")
    if "error" in d:
        sys.exit(f"Gemini chyba: {d['error'].get('status')} {d['error'].get('message', '')[:300]}")
    for c in d.get("candidates", []):
        for part in c.get("content", {}).get("parts", []):
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])
    sys.exit("Gemini nevrátil obrázok.")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    from PIL import Image
    post_path = Path(sys.argv[1])
    post = json.loads(post_path.read_text(encoding="utf-8"))
    missing = [l for l, L in post["langs"].items() if not L.get("image_alt")]
    if missing:
        sys.exit(f"Najprv doplň langs.<jazyk>.image_alt (chýba: {', '.join(missing)}).")
    im = Image.open(io.BytesIO(generate(sys.argv[2]))).convert("RGB")
    out_dir = ROOT / "assets" / "blog"
    out_dir.mkdir(parents=True, exist_ok=True)
    big = out_dir / f"{post['id']}.webp"
    small = out_dir / f"{post['id']}-640.webp"
    im.save(big, "WEBP", quality=82, method=6)
    im.resize((640, round(640 * im.height / im.width)), Image.LANCZOS).save(small, "WEBP", quality=80, method=6)
    share = out_dir / f"{post['id']}.jpg"  # pre zdieľanie (LinkedIn a iné nevedia WebP)
    im.save(share, "JPEG", quality=85, optimize=True, progressive=True)
    post["image"] = {"file": f"assets/blog/{big.name}", "thumb": f"assets/blog/{small.name}",
                     "share": f"assets/blog/{share.name}", "width": im.width, "height": im.height}
    post_path.write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK {big.relative_to(ROOT)} {im.width}x{im.height}, {big.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
