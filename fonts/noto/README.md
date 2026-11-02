# Fallback fonts for the optional languages

Self-hosted, subset Noto fonts used by `/langfonts.css` (SIL Open Font License 1.1; licence texts are in this folder).
Atkinson Hyperlegible Next has Latin only: no Cyrillic, Indic or Arabic script, and it lacks half the Vietnamese letters.

| File | Used for | Source | Size |
|---|---|---|---|
| `NotoSans-Cyrillic.woff2` | Russian (`/ru/`) | Noto Sans 2.015 | 12.3 KB |
| `NotoSans-Vietnamese.woff2` | Vietnamese (`/vi/`): Basic Latin + Vietnamese | Noto Sans 2.015 | 45.0 KB |
| `NotoSansDevanagari.woff2` | Hindi (`/hi/`) | Noto Sans Devanagari 2.007 | 73.1 KB |
| `NotoSansBengali.woff2` | Bengali (`/bn/`) | Noto Sans Bengali 3.011 | 68.4 KB |
| `NotoNaskhArabic.woff2` | Urdu (`/ur/`) | Noto Naskh Arabic 2.021 | 45.6 KB |

Each is one variable font (weights 400-700), so regular and bold come from one file. A page loads only the file for its own language.
Indonesian, Turkish and Italian need no extra font. Rebuild with `tools/fonts/make_lang_fonts.py`.
