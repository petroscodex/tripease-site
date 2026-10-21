# Translations (9 languages)

The English pages stay the source. Edit them as usual; the build writes the translated copies.

| Folder | Language | Notes |
|---|---|---|
| `/` | English | source |
| `/zh-hans/` | 简体中文 | mainland China and Singapore. **China-facing: the build fails if the page mentions Taiwan** (marketing rule, Peter 21 Oct 2026) |
| `/zh-hant/` | 繁體中文 | written for Taiwan usage; also Hong Kong and Macau |
| `/ja/` `/ko/` `/th/` `/de/` `/fr/` `/es/` | | German uses *du*, French *vous*, Spanish *tú* |

## Day to day

```sh
pip install beautifulsoup4==4.15.0
python3 tools/i18n/build.py build      # after any change to a translated English page
python3 tools/i18n/build.py check      # same, but fails if a translation is missing (CI runs this)
python3 tools/i18n/build.py extract    # refresh i18n/source.json: every string to translate
```

* Change English text → the build reports the string as missing in each language and shows the
  **English** text there until it is translated. Nothing breaks.
* Translations live in `i18n/<lang>.json`: `"English text": "translation"`. Links and bold text
  inside a sentence appear as plain `<a>…</a>` / `<b>…</b>`; keep the same tags, word order can
  change. The build puts the link addresses back.
* The language menu, `hreflang` links, canonical URLs, `og:locale` and the sitemap are written by
  the build. In the English page it only touches those lines.
* `site.js` text (the passport checker, price toggle) comes from the `js` block of each language
  file; English is the fallback. Placeholders like `{d}` must stay.

## Which pages

`PAGES` in `build.py`. Today: the home page. Next: `arrival-forms.html` and the 13 arrival guides
(high search value), then help, press, 404. Legal pages (privacy, terms) stay English until a
lawyer or native speaker has checked a translation.

## Before going live

All 8 translations are **drafts by Claude (21 Oct 2026)**. Have a native speaker check at least the
pricing, FAQ and legal lines in each language, because they make promises.

Fonts: Atkinson Hyperlegible has no CJK or Thai glyphs, so `home.css` names system fonts per
language (`html:lang(...)`). Nothing loads from Google: fine for mainland China.
