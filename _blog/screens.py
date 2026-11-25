#!/usr/bin/env python3
"""Prevedie screenshoty návodov z _navody-screens/*.png do assets/navody/*.webp (šírka 600 px).

Použitie: python3 _blog/screens.py   (potom python3 _blog/build.py)
Názov súboru: <č.návodu>-<krok>-<jazyk>.png, napr. 07-2-sk.png → assets/navody/07-2-sk.webp
"""
import re
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "_navody-screens", ROOT / "assets" / "navody"
OUT.mkdir(parents=True, exist_ok=True)
n = 0
for f in sorted(SRC.glob("*.png")):
    if not re.fullmatch(r"\d{2}-\d+-(sk|cs|en)\.png", f.name):
        print("preskočené (zlý názov):", f.name)
        continue
    im = Image.open(f).convert("RGB")
    if im.width > 600:
        im = im.resize((600, round(600 * im.height / im.width)), Image.LANCZOS)
    im.save(OUT / (f.stem + ".webp"), "WEBP", quality=82, method=6)
    n += 1
print(f"Hotovo: {n} screenshotov v assets/navody/")
