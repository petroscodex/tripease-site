#!/usr/bin/env python3
"""Rebuilds fonts/noto/*.woff2 (the self-hosted fallback fonts for hi, ru, vi, bn, ur; see /langfonts.css).

  pip install fonttools brotli
  python3 tools/fonts/make_lang_fonts.py <folder with the four source .ttf files>

Sources (SIL Open Font License 1.1, copied to fonts/noto/OFL-*.txt), from github.com/google/fonts, ofl/ folder, commit 8b0a1d0:
  NotoSans[wdth,wght].ttf (2.015)  NotoSansDevanagari[wdth,wght].ttf (2.007)  NotoSansBengali[wdth,wght].ttf (3.011)  NotoNaskhArabic[wght].ttf (2.021)
Save them in the folder as NotoSans.ttf, NotoSansDevanagari.ttf, NotoSansBengali.ttf, NotoNaskhArabic.ttf.
Each font is pinned to normal width and weights 400-700 (still a variable font, so one file covers regular and bold), subset to the
ranges below, with all OpenType layout features kept (Indic conjuncts and Arabic joining need them), hinting dropped, written as woff2.
The ranges must match the unicode-range in langfonts.css."""
import os
import subprocess
import sys
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

src = sys.argv[1]
out = os.path.join(os.path.dirname(__file__), "..", "..", "fonts", "noto")
os.makedirs(out, exist_ok=True)
PIN = {"NotoSans": {"wdth": 100, "wght": (400, 700)}, "NotoSansDevanagari": {"wdth": 100, "wght": (400, 700)},
       "NotoSansBengali": {"wdth": 100, "wght": (400, 700)}, "NotoNaskhArabic": {"wght": (400, 700)}}
SETS = {  # output name: (source font, unicode ranges)
    "NotoSans-Cyrillic": ("NotoSans", "U+0400-045F,U+0490-0491,U+0301,U+2116"),
    "NotoSans-Vietnamese": ("NotoSans", "U+0020-007E,U+00A0-00FF,U+0100-017F,U+0192,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303,U+0309,U+0323,U+1EA0-1EF9,U+20AB,U+2010-2027"),
    "NotoSansDevanagari": ("NotoSansDevanagari", "U+0900-097F,U+A8E0-A8FF,U+200C-200D,U+25CC"),
    "NotoSansBengali": ("NotoSansBengali", "U+0980-09FF,U+0964-0965,U+200C-200D,U+25CC"),
    "NotoNaskhArabic": ("NotoNaskhArabic", "U+0600-06FF,U+0750-077F,U+200C-200F,U+25CC"),
}
tmp = {}
for name, axes in PIN.items():
    tmp[name] = os.path.join(src, f"pinned-{name}.ttf")
    instancer.instantiateVariableFont(TTFont(os.path.join(src, f"{name}.ttf")), axes).save(tmp[name])
for name, (font, ranges) in SETS.items():
    dst = os.path.join(out, f"{name}.woff2")
    subprocess.check_call(["pyftsubset", tmp[font], f"--unicodes={ranges}", "--layout-features=*", "--flavor=woff2",
                           "--name-IDs=*", "--no-hinting", "--notdef-outline", f"--output-file={dst}"])
    print(f"{name}.woff2  {os.path.getsize(dst)} bytes")
