# Translations (11 languages)

The English pages stay the source. Edit them as usual; the build writes the translated copies.

| Folder | Language | Notes |
|---|---|---|
| `/` | English | source |
| `/zh-hans/` | 简体中文 | mainland China and Singapore. **China-facing: the build fails if the page mentions a blocked region term** (marketing rule) |
| `/zh-hant/` | 繁體中文 | Traditional Chinese wording; also Hong Kong and Macau |
| `/ja/` `/ko/` `/th/` `/de/` `/fr/` `/es/` | | German uses *du*, French *vous*, Spanish *tú* |
| `/ar/` | العربية | Modern Standard Arabic, **right-to-left**. See *Arabic and RTL* below |
| `/pt-br/` | Português (Brasil) | Brazilian Portuguese, *você*; `lang="pt-BR"`, hreflang `pt-BR`. Prices stay in US$. Like Arabic it has `land/`, `help.html` and `creators/` (noindex). **Machine draft: needs a native-speaker review** |

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
* On a phone (820 px and below) the header links and the language list open from the menu button (`menu.js`, styles at the end of `home.css`). The footer list stays too.
* On a phone the header also has a globe language button right next to "Get the app" (`.lang-btn`, written by `menu_html` in `build.py`). It opens the language list on its own; the menu button still shows links and languages. At 340 px and below the TripEase wordmark is visually hidden (logo only) so "Get the app", the globe and the menu button all fit.
* English-only pages (`STATIC_EN` in `build.py`: press, 404, tipping, plugs, local apps) get the same language menu, linking to each language's home page. Privacy and terms link to the footer list on the home page.
* `site.js` text (the passport checker, price toggle) comes from the `js` block of each language
  file; English is the fallback. Placeholders like `{d}` must stay.

## Optional languages: hi, id, ru, tr, it, vi, bn, ur

Hindi (`/hi/`), Bahasa Indonesia (`/id/`), Russian (`/ru/`), Turkish (`/tr/`), Italian (`/it/`), Vietnamese (`/vi/`), Bengali (`/bn/`) and Urdu (`/ur/`, right-to-left)
are registered in `LANGS` and listed in `OPTIONAL` in `build.py`, but they only go live when their translation is ready.

**The 95% rule.** For an optional language the build counts the strings of the pages that language has (`PAGES`, plus its `EXTRA` pages if any)
and the script strings (`js_strings.json`), and checks how many have a translation in `i18n/<lang>.json` (`MIN_COVERAGE` in `build.py`).

| `i18n/<lang>.json` | What the build does |
|---|---|
| missing, unreadable, or under 95% of the strings | Skips the language silently: no `/<lang>/` pages (an old folder is deleted), no entry in the language menu or footer list, no `hreflang`, no sitemap entry. It prints `<lang>: skipped (...)`. `check` passes. |
| 95% or more | Language is live. The menu, footer list, `hreflang` links and sitemap entries for it appear on every page, and `/<lang>/` pages are written. Strings without a translation stay English. |

`check` is strict for the first ten languages (any missing string fails CI), as before. For an optional language that is live it only prints a
`note:` and the first 10 missing strings, so a language at 96% does not break the build. Fill the gaps anyway. Privacy and terms stay English in every language.
The footer FAQ and any "11 languages" wording on the site are edited by hand, not by the build.

**Adding a language** (either one of the eight above, or a new one):
1. New language only: add it to `LANGS` (folder, BCP-47 code, native menu label, `html lang`), to `OPTIONAL` and to `LANG_CSS`; add its short code to `SHORT` and the word "Language" to `LANG_WORD`; add it to `RTL` if it is right-to-left.
2. Make `i18n/<lang>.json` (same format as the others; `python3 tools/i18n/build.py extract` lists every string). Placeholders such as `{d}` and the inline tags (`<a>`, `<b>`) must stay.
3. `python3 tools/i18n/build.py build`, then commit the generated `/<lang>/` folder, the changed English pages (menu and hreflang lines) and `sitemap.xml`. CI fails if they are not committed.
4. Check the fonts: see below. Check the pages on a phone, and in a right-to-left language mirror and read them from the right.

**Fonts.** Optional-language pages also load `/langfonts.css` (added by the build; English and the older languages never load it). It declares per-language
font stacks and the self-hosted fallbacks in `fonts/noto/` (Noto, SIL OFL, licence texts next to the files; rebuild with `tools/fonts/make_lang_fonts.py`).
Atkinson Hyperlegible Next covers Latin only, so Indonesian, Turkish and Italian need nothing extra. Hindi, Bengali, Urdu, Russian and Vietnamese each load one
subset font (12 to 73 KB, woff2) and only on their own pages, because each `@font-face` has a `unicode-range` and each family is named in one language's stack only.
Urdu uses Noto Naskh Arabic (clearer on phones than Nastaliq). Vietnamese uses Noto Sans for all of its Latin text, because Atkinson lacks half the letters
and two fonts in one word look uneven.

**Right-to-left.** `RTL` in `build.py` lists the languages that get `dir="rtl"` and `/rtl.css`. The rules in `rtl.css` apply to `html[dir="rtl"]`, so a new right-to-left language
needs only its font stack (in `langfonts.css`). The breadcrumb chevron is flipped in CSS. In translated running text write the right-to-left arrow as `‹` instead of `›` (for example in a Settings path), because the character does not mirror by itself.

## Which pages

`PAGES` in `build.py`. Today: the home page. Next: `arrival-forms.html` and the 13 arrival guides
(high search value), then help, press, 404. Legal pages (privacy, terms) stay English until a
lawyer or native speaker has checked a translation.

## Before going live

All 8 translations are **drafts by Claude (21 Oct 2026)**. Have a native speaker check at least the
pricing, FAQ and legal lines in each language, because they make promises.

Fonts: Atkinson Hyperlegible has no CJK or Thai glyphs, so `home.css` names system fonts per
language (`html:lang(...)`). Nothing loads from Google: fine for mainland China.

## Arabic and RTL

* `/ar/` pages get `<html lang="ar" dir="rtl">` and load `/rtl.css` (only on Arabic pages).
* The shared CSS (`styles.css`, `home.css`) uses logical properties (`margin-inline-start`,
  `inset-inline-end`, ...), so English renders exactly as before and Arabic mirrors by itself.
  `rtl.css` holds only the Arabic extras: font stack (system Arabic fonts; Atkinson has no Arabic
  glyphs), taller line-height, no letter-spacing, and mirrored hero image and gradients.
  Logos, screenshots and photos are not mirrored (the hero photo is, so the plane stays visible).
* Latin runs (TripEase, Petros Codex, prices, airline and form codes, dates, e-mail, URLs) are wrapped
  in `<bdi>` by the build so the surrounding Arabic punctuation does not jumble them.
  `EXTRA` in `build.py` lists pages that exist **only** in some languages (Arabic and Brazilian Portuguese: `land/`, `help.html`,
  `creators/`); the language menu, hreflang and sitemap follow that list. The English copy of those pages
  gets a language menu from `patch_english`.
* `placeholder` attributes are translated (help search); e-mail examples are skipped.
* Privacy and terms stay English. Tipping, local apps, plugs, press and 404 are not translated yet.
* `i18n/ar.json` is a **draft that needs a native-speaker review**, above all the pricing, FAQ,
  creators (payout, tax, terms) and the country, authority and airport names.
