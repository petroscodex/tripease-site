#!/usr/bin/env python3
"""Builds the translated site from the English pages. Zan keeps editing the English HTML;
nothing else about the site changes.

  python3 tools/i18n/build.py extract   # writes i18n/source.json: every string to translate
  python3 tools/i18n/build.py build     # writes /<lang>/... pages, hreflang, language menu, sitemap
  python3 tools/i18n/build.py check     # build + fail if any translation is missing (for CI)

How it works
* A "segment" is the innermost block (p, h1-h6, li, label, button, a, ...) that holds text. Its
  inner HTML, whitespace-normalised, is the key; the translation is HTML with the same inline tags,
  so word order can change (Chinese, Japanese, Korean, Thai need that). Text outside any block,
  alt/title/aria-label, the <title>, meta descriptions and the JSON-LD strings are translated too.
* i18n/<lang>.json maps English -> translation. A missing string stays English and is reported,
  so editing the English page never breaks a translated one.
* Links: anchors to a page that exists in that language point to it; everything else points to
  the English page. Relative URLs become root-relative so they work from /<lang>/.
* China-facing rule: the Simplified Chinese pages must not mention the blocked region terms in BLOCKED (build fails if they do).
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

import bs4
from bs4 import BeautifulSoup, Comment, NavigableString

ROOT = Path(__file__).resolve().parents[2]
I18N = ROOT / "i18n"
SITE = "https://tripeaseapp.com"
# English source pages that have translations. Add more as their strings get translated.
PAGES = ["index.html", "arrival-forms.html", "arrival/index.html"] + sorted(
    str(p.relative_to(ROOT)) for p in [*ROOT.glob("arrival-*.html"), *ROOT.glob("arrival/*/index.html")]
    if p.name != "arrival-forms.html")
LANGS = {  # url folder: (BCP-47 code, menu label, html lang attribute)
    "zh-hans": ("zh-Hans", "简体中文", "zh-Hans"),
    "zh-hant": ("zh-Hant", "繁體中文", "zh-Hant"),
    "ja": ("ja", "日本語", "ja"),
    "ko": ("ko", "한국어", "ko"),
    "th": ("th", "ไทย", "th"),
    "de": ("de", "Deutsch", "de"),
    "fr": ("fr", "Français", "fr"),
    "es": ("es", "Español", "es"),
    "ar": ("ar", "العربية", "ar"),
    "pt-br": ("pt-BR", "Português (Brasil)", "pt-BR"),
}
# English-only pages that still get the language menu (header and footer), with links to each language's home page.
STATIC_EN = ["press.html", "404.html", "tipping/index.html", "plugs/index.html", "local-apps/index.html"]
RTL = {"ar"}  # right-to-left: the build adds dir="rtl" and /rtl.css
# Pages that exist in one language only (besides PAGES). Arabic also has the land page, the help page and
# the creators page. The legal pages (privacy, terms) stay English until a lawyer or native speaker has checked a translation.
EXTRA = {"ar": ["land/index.html", "help.html", "creators/index.html"],
         "pt-br": ["land/index.html", "help.html", "creators/index.html"]}
ALL_PAGES = PAGES + list(dict.fromkeys(p for ps in EXTRA.values() for p in ps if p not in PAGES))  # each extra page once, even if several languages have it


def pages_in(lang: str) -> list[str]:
    return PAGES + EXTRA.get(lang, [])


def langs_for(page: str) -> list[str]:
    return [k for k in LANGS if page in pages_in(k)]


def indexed(page: str) -> bool:
    """False for share-by-link pages (robots noindex): no hreflang and no sitemap entry for them."""
    return "noindex" not in (ROOT / page).read_text(encoding="utf-8")
CHINA_FACING = {"zh-hans"}
# Region terms the China-facing pages must not contain. Kept as escapes so this public file does not spell them out.
BLOCKED = re.compile("\u0054\u0061\u0069\u0077\u0061\u006e|\u53f0\u6e7e|\u81fa\u7063|\u53f0\u7063", re.I)
# A segment is the innermost block holding text; links inside it stay part of the sentence.
BLOCK = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "dt", "dd", "td", "th", "caption", "summary",
         "label", "legend", "button", "figcaption", "title", "option"}
SEG = BLOCK | {"a"}  # a link is its own segment only when it isn't inside a block
INLINE = {"a", "b", "strong", "em", "i", "span", "small", "br", "code", "abbr"}
ATTRS = ("alt", "title", "aria-label", "placeholder")  # placeholder: only the help-search hint; e-mail examples are skipped
META = {("name", "description"), ("property", "og:title"), ("property", "og:description"),
        ("property", "og:image:alt"), ("name", "twitter:title"), ("name", "twitter:description")}
JSONLD_KEYS = {"alternateName", "description", "slogan", "featureList", "name", "text", "headline"}
LD_NAMED = {"Question", "ListItem", "Country"}  # types whose "name" is prose, not a brand
HAS_WORDS = re.compile(r"[A-Za-z]")
BRAND = {"TripEase", "Petros Codex", "EN"}
# Same in every language: airport codes, plug types, handles, names of publications and datasets.
SOCIAL = r"(?:TikTok|Instagram|YouTube|X)"
KEEP = re.compile(r"^(?:[A-Z]{3}(?: · [A-Z]{3})*|" + SOCIAL + r"(?: · " + SOCIAL + r")+|[A-N](?:, [A-N])* · \d+ V|(?:TikTok|Instagram|YouTube|X)(?: @\S+)?"
                  r"|Bangkok Post|Khaosod English|TravelRequirements\.info Entry Requirements Dataset|SIL Open Font License)$")
LANG_UI = ("lang", "foot-langs", "lang-btn")  # the language menu itself is never translated


def norm(s: str) -> str:
    return " ".join(s.split())


URLISH = re.compile(r"^(?:https?://\S+|[a-z0-9-]+(?:\.[a-z0-9-]+)+(?:/\S*)?)$")  # links and domains stay as written


def skip_attr(name: str, text: str) -> bool:
    return skip(text) or (name == "placeholder" and "@" in text)


def skip(text: str) -> bool:
    return text in BRAND or bool(KEEP.match(text)) or bool(URLISH.match(text)) or not HAS_WORDS.search(text)


def in_lang_ui(el) -> bool:
    return any(c in LANG_UI for p in [el, *el.parents] if getattr(p, "get", None) for c in (p.get("class") or []))


def soup(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def bare(node) -> str:
    """HTML of a node with the attributes of inline tags removed: translators never see URLs or styles."""
    if isinstance(node, Comment):
        return ""
    if isinstance(node, NavigableString):
        return str(node).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if node.name == "br":
        return "<br>"
    return f"<{node.name}>" + "".join(bare(c) for c in node.contents) + f"</{node.name}>"


def inner(el) -> str:
    return norm("".join(bare(c) for c in el.contents))


def restore_attrs(src_el, frag) -> bool:
    """Copy attributes from the English inline tags onto the translation's tags, matched in order per
    tag name. False if the translation doesn't have the same tags."""
    src = [t for t in src_el.find_all(True)]
    dst = [t for t in frag.find_all(True)]
    if sorted(t.name for t in src) != sorted(t.name for t in dst):
        return False
    by_name = {}
    for t in src:
        by_name.setdefault(t.name, []).append(t.attrs)
    for t in dst:
        t.attrs = dict(by_name[t.name].pop(0))
    return True


def segments(doc: BeautifulSoup):
    """Innermost text-holding blocks, in document order."""
    for el in doc.find_all(SEG):
        if el.find_parent(["script", "style"]) or el.find(BLOCK) or in_lang_ui(el):
            continue
        if el.name == "a" and el.find_parent(BLOCK):
            continue
        if not skip(norm(el.get_text())):
            yield el


def loose_texts(doc: BeautifulSoup):
    for t in doc.find_all(string=True):
        if isinstance(t, Comment) or t.parent.name in ("script", "style", "[document]"):
            continue
        if any(p.name in BLOCK for p in t.parents if p.name) or t.find_parent("a"):
            continue
        x = norm(t)
        if not skip(x) and not in_lang_ui(t.parent):
            yield t, x


def ld_translatable(o: dict, k: str, v) -> bool:
    """JSON-LD fields we translate: descriptions, slogans, FAQ questions and answers."""
    if not isinstance(v, str) or skip(norm(v)):
        return False
    if k == "name":
        return o.get("@type") in LD_NAMED
    return k in JSONLD_KEYS


def jsonld_strings(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "featureList" and isinstance(v, list):
                out.extend(norm(x) for x in v if isinstance(x, str))
            elif ld_translatable(obj, k, v):
                out.append(norm(v))
            else:
                jsonld_strings(v, out)
    elif isinstance(obj, list):
        for x in obj:
            jsonld_strings(x, out)
    return out


def strings(doc: BeautifulSoup) -> list[str]:
    out = [inner(el) for el in segments(doc)]
    out += [x for _, x in loose_texts(doc)]
    for el in doc.find_all(True):
        if in_lang_ui(el):
            continue
        out += [norm(el[a]) for a in ATTRS if el.get(a) and not skip_attr(a, norm(el[a]))]
        if el.name == "meta" and any(el.get(k) == v for k, v in META) and el.get("content"):
            out.append(norm(el["content"]))
    for s in doc.find_all("script", type="application/ld+json"):
        out += jsonld_strings(json.loads(s.string), [])
    return list(dict.fromkeys(out))


JS_STRINGS = json.loads((Path(__file__).parent / "js_strings.json").read_text(encoding="utf-8"))


def cmd_extract() -> None:
    src = {}
    for page in ALL_PAGES:
        for s in strings(soup(ROOT / page)):
            src.setdefault(s, []).append(page)
    I18N.mkdir(exist_ok=True)
    (I18N / "source.json").write_text(json.dumps({"_note": "Generated by tools/i18n/build.py extract. "
        "Keys are the English strings; translate them in i18n/<lang>.json.", "strings": src, "js": JS_STRINGS},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"extract: {len(src)} strings from {len(ALL_PAGES)} page(s), {len(JS_STRINGS)} script strings")


def url_for(page: str, lang: str | None) -> str:
    """index.html pages are served as their folder: arrival/japan/index.html -> /arrival/japan/."""
    path = "/" + (page[: -len("index.html")] if page.endswith("index.html") else page)
    return path if not lang else f"/{lang}{path}"


def plain(html: str) -> str:
    return norm(BeautifulSoup(html, "html.parser").get_text())


def _names(page: str):
    return [(None, "en", "English")] + [(k, LANGS[k][0], LANGS[k][1]) for k in langs_for(page)]


def _names_home():
    return [(None, "en", "English")] + [(k, LANGS[k][0], LANGS[k][1]) for k in LANGS]


def _cur(k, cur) -> str:
    return ' aria-current="true"' if k == cur else ""


def _items(page: str, cur: str | None, home: bool):
    """Language links for a page; on an English-only page (home) every other language links to its home page."""
    return [((url_for(page, None) if k is None else f"/{k}/") if home else url_for(page, k), code, label, k)
            for k, code, label in (_names_home() if home else _names(page))]


# Phone language button: short code next to the globe, and the button's name in each language.
SHORT = {None: "EN", "zh-hans": "简", "zh-hant": "繁", "ja": "日", "ko": "한", "th": "ไทย", "de": "DE", "fr": "FR", "es": "ES", "ar": "AR", "pt-br": "PT"}
LANG_WORD = {None: "Language", "zh-hans": "语言", "zh-hant": "語言", "ja": "言語", "ko": "언어", "th": "ภาษา", "de": "Sprache",
             "fr": "Langue", "es": "Idioma", "ar": "اللغة", "pt-br": "Idioma"}
GLOBE = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
         'aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="9.5"/><path d="M2.5 12h19M12 2.5c-2.7 2.6-4 5.8-4 9.5s1.3 6.9 4 9.5c2.7-2.6 4-5.8 4-9.5s-1.3-6.9-4-9.5z"/></svg>')


def menu_html(page: str, cur: str | None, home: bool = False) -> str:
    cur_label = "EN" if not cur else LANGS[cur][1]
    items = "".join('<li><a href="%s" hreflang="%s" lang="%s"%s>%s</a></li>' % (u, code, code, _cur(k, cur), label)
                    for u, code, label, k in _items(page, cur, home))
    btn = ('<button class="lang-btn" type="button" aria-label="%s" aria-expanded="false" hidden>%s<span class="lang-code" aria-hidden="true">%s</span></button>'
           % (LANG_WORD[cur], GLOBE, SHORT[cur]))
    return '<details class="lang"><summary aria-label="Language">' + cur_label + "</summary><ul>" + items + "</ul></details>" + btn


def foot_html(page: str, cur: str | None, home: bool = False) -> str:
    links = " \u00b7 ".join('<a href="%s" hreflang="%s" lang="%s"%s>%s</a>' % (u, code, code, _cur(k, cur), label)
                        for u, code, label, k in _items(page, cur, home))
    return '<nav class="foot-langs" id="languages" aria-label="Language">' + links + "</nav>"


def alt_links(page: str) -> list[tuple[str, str]]:
    if not indexed(page):
        return []
    return [("en", url_for(page, None))] + [(LANGS[k][0], url_for(page, k)) for k in langs_for(page)] + [("x-default", url_for(page, None))]


def alt_html(page: str) -> str:
    links = alt_links(page)
    return "\n".join(f'  <link rel="alternate" hreflang="{c}" href="{SITE}{u}" />' for c, u in links)


def patch_english(page: str, home: bool = False) -> None:
    """The English page is Zan's hand-written source: change only the language links, the header menu
    and the footer list, as text, so the rest of the file stays byte-for-byte as she wrote it."""
    path = ROOT / page
    x = path.read_text(encoding="utf-8")
    if not home:  # an English-only page has no translations to point search engines at
        x = re.sub(r'\n[ \t]*<link rel="alternate" hreflang="[^"]*" href="[^"]*" ?/?>', "", x)
        x = re.sub(r'(<link rel="canonical"[^>]*>)', lambda m: m.group(1) + ("\n" + alt_html(page) if alt_html(page) else ""), x, count=1)
    x = re.sub(r'(?:<button class="lang"[^>]*>.*?</button>|<details class="lang">.*?</details>)(?:\s*<button class="lang-btn".*?</button>)?',
               lambda m: menu_html(page, None, home), x, count=1, flags=re.S)
    x = re.sub(r'<nav class="foot-langs".*?</nav>\n?[ \t]*', "", x, flags=re.S)
    x = re.sub(r'([ \t]*)(<div class="legal-lines">)', lambda m: m.group(1) + foot_html(page, None, home) + "\n" + m.group(1) + m.group(2), x, count=1)
    path.write_text(x, encoding="utf-8")


def lang_menu(doc: BeautifulSoup, page: str, cur: str | None) -> None:
    """Header menu (desktop) and footer list (every screen size) in a generated page."""
    for old_btn in doc.find_all(class_="lang-btn"):
        old_btn.decompose()
    btn = doc.find(class_="lang")
    if btn is not None:
        btn.replace_with(BeautifulSoup(menu_html(page, cur), "html.parser"))
    old = doc.find(class_="foot-langs")
    if old is not None:
        old.decompose()
    legal = doc.find(class_="legal-lines")
    if legal is not None:
        legal.insert_before(BeautifulSoup(foot_html(page, cur), "html.parser"))


def alternates(doc: BeautifulSoup, page: str, cur: str | None) -> None:
    head = doc.head
    for l in head.find_all("link", rel="alternate"):
        if l.get("hreflang"):
            ws = l.next_sibling
            if isinstance(ws, NavigableString) and not ws.strip():
                ws.extract()  # the line break before the next tag, so rebuilds don't add blank lines
            l.decompose()
    canon = head.find("link", rel="canonical")
    anchor = canon
    for code, path in alt_links(page):
        tag = doc.new_tag("link", rel="alternate", hreflang=code, href=SITE + path)
        anchor.insert_after(tag); anchor.insert_after("\n  "); anchor = tag
    canon["href"] = SITE + url_for(page, cur)


def fix_url(u: str) -> str:
    if not u or re.match(r"^([a-z]+:|/|#|\?)", u):
        return u
    return "/" + u


APP_SHOT = re.compile(r"/assets/app/([a-z0-9-]+-(?:390|780)\.webp)")


def localize_shots(doc: BeautifulSoup, lang: str) -> None:
    """Point app screenshots at /assets/app/<lang>/ when that language has its own render of the file.

    Anything without a localized file keeps the English /assets/app/ one. Covers img src/srcset, any
    preload/meta URL and the JSON-LD "screenshot" URLs; width/height/loading attributes are not touched.
    """
    def swap(m: re.Match) -> str:
        return f"/assets/app/{lang}/{m.group(1)}" if (ROOT / "assets/app" / lang / m.group(1)).is_file() else m.group(0)

    for el in doc.find_all(True):
        for attr in ("src", "srcset", "href", "content", "data-src", "imagesrcset"):
            v = el.get(attr)
            if isinstance(v, str) and "/assets/app/" in v:
                el[attr] = APP_SHOT.sub(swap, v)
    for s in doc.find_all("script", type="application/ld+json"):
        if s.string and "/assets/app/" in s.string:
            s.string = APP_SHOT.sub(swap, s.string)


def translate_page(page: str, lang: str, tr: dict, missing: set) -> BeautifulSoup:
    doc = soup(ROOT / page)
    code, _, html_lang = LANGS[lang]

    def t(s: str) -> str:
        if s in tr:
            return tr[s]
        missing.add(s)
        return s

    for el in list(segments(doc)):
        key = inner(el)
        if key in tr:
            frag = BeautifulSoup(tr[key], "html.parser")
            if not restore_attrs(el, frag):
                missing.add(key)
                continue
            el.clear()
            for c in list(frag.contents):
                el.append(c)
        else:
            missing.add(key)
    for node, key in list(loose_texts(doc)):
        if key in tr:
            lead = " " if node[:1].isspace() else ""
            trail = " " if node[-1:].isspace() else ""
            node.replace_with(NavigableString(lead + tr[key] + trail))
        else:
            missing.add(key)
    for el in doc.find_all(True):
        for a in ATTRS:
            if el.get(a) and not skip_attr(a, norm(el[a])) and not in_lang_ui(el):
                el[a] = plain(t(norm(el[a])))
        if el.name == "meta" and any(el.get(k) == v for k, v in META) and el.get("content"):
            el["content"] = plain(t(norm(el["content"])))
        for a in ("href", "src"):
            if el.get(a):
                el[a] = fix_url(el[a])
        if el.get("srcset"):
            el["srcset"] = ", ".join(fix_url(p.strip().split(" ")[0]) + (" " + " ".join(p.strip().split(" ")[1:]) if len(p.strip().split(" ")) > 1 else "") for p in el["srcset"].split(","))
    # Links into pages that exist in this language stay in this language; the rest go to English.
    for a in doc.find_all("a", href=True):
        path, frag = (a["href"].split("#", 1) + [None])[:2]
        if path.startswith(SITE + "/"):
            path = path[len(SITE):]
        for p in pages_in(lang):
            if path in {url_for(p, None), "/" + p} or (p == "index.html" and path == ""):
                if path == "" and frag is not None:
                    break  # same-page anchor (#pricing): already fine
                a["href"] = url_for(p, lang) + (f"#{frag}" if frag is not None else "")
                break
    site_urls = {SITE + url_for(p, None): SITE + url_for(p, lang) for p in pages_in(lang)}
    for s in doc.find_all("script", type="application/ld+json"):
        data = json.loads(s.string)

        def walk(o):
            if isinstance(o, dict):
                for k, v in list(o.items()):
                    if k == "featureList" and isinstance(v, list):
                        o[k] = [plain(t(norm(x))) for x in v]
                    elif ld_translatable(o, k, v):
                        o[k] = plain(t(norm(v)))
                    elif k == "inLanguage" and isinstance(v, str):
                        o[k] = code
                    elif k in ("url", "item") and isinstance(v, str) and v in site_urls:
                        o[k] = site_urls[v]
                    else:
                        walk(v)
            elif isinstance(o, list):
                for x in o:
                    walk(x)
        walk(data)
        s.string = json.dumps(data, ensure_ascii=False)
    localize_shots(doc, lang)
    doc.html["lang"] = html_lang
    if lang in RTL:
        doc.html["dir"] = "rtl"
        isolate_latin(doc)
        css = doc.find("link", rel="stylesheet", href=re.compile(r"(^|/)(home|styles)\.css$"))
        if css is not None and doc.find("link", href="/rtl.css") is None:
            css.insert_after(doc.new_tag("link", rel="stylesheet", href="/rtl.css"))
            css.insert_after("\n  ")
    og = doc.find("meta", property="og:url")
    if og:
        og["content"] = SITE + url_for(page, lang)
    doc.head.append(doc.new_tag("meta", property="og:locale", content=code.replace("-", "_")))
    return doc


ARABIC = re.compile("[\u0600-\u06FF]")
# A run of Latin text: words, digits and the punctuation inside names, e-mail addresses and web addresses.
_WORD = r"US\$[0-9][0-9.,]*|@?[A-Za-z][A-Za-z0-9]*(?:[._\-/:@#+&']+[A-Za-z0-9]+)*"
_RUN = r"(?:" + _WORD + r")(?: (?:" + _WORD + r")| [0-9][0-9.,]*(?![0-9A-Za-z]))*"
_MONEY = r"\$[0-9][0-9.,]*(?:\u2013\$[0-9][0-9.,]*)?"
LATIN_RUN = re.compile(_MONEY + r"|\(" + _RUN + r"\)|" + _RUN)  # a Latin run inside brackets keeps its brackets
BIDI_SKIP = {"script", "style", "title", "bdi", "code", "textarea", "option"}
BIDI_BLOCKS = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "dt", "dd", "summary", "figcaption", "label", "button", "blockquote", "div"}


def isolate_latin(doc: BeautifulSoup) -> None:
    """Right-to-left pages: wrap each run of Latin text (TripEase, TDAC, e-mail and web addresses, US$ prices) in <bdi>,
    so punctuation next to it cannot jump to the wrong side of the run."""
    body = doc.body
    if body is None:
        return
    for node in list(body.find_all(string=True)):
        if not isinstance(node, NavigableString) or isinstance(node, Comment):
            continue
        if node.parent.name in BIDI_SKIP or node.parent.find_parent(BIDI_SKIP) is not None or not LATIN_RUN.search(str(node)):
            continue
        block = node.parent
        while block is not None and block.name not in BIDI_BLOCKS:
            block = block.parent
        if block is None or not ARABIC.search(block.get_text()):
            continue
        text, pos, parts = str(node), 0, []
        for m in LATIN_RUN.finditer(text):
            parts.append(NavigableString(text[pos:m.start()]))
            b = doc.new_tag("bdi")
            b.string = m.group(0)
            parts.append(b)
            pos = m.end()
        parts.append(NavigableString(text[pos:]))
        for part in parts:
            node.insert_before(part)
        node.extract()


def inject_js(doc: BeautifulSoup, js: dict) -> None:
    if not js:
        return
    tag = doc.new_tag("script")
    tag.string = "window.TE_L10N=" + json.dumps(js, ensure_ascii=False) + ";"
    site_js = doc.find("script", src="/site.js")
    (site_js.insert_before if site_js else doc.body.append)(tag)


def write(doc: BeautifulSoup, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    html = str(doc)
    if not html.lstrip().lower().startswith("<!doctype"):
        html = "<!DOCTYPE html>\n" + html
    path.write_text(html, encoding="utf-8")


def sitemap() -> None:
    p = ROOT / "sitemap.xml"
    x = p.read_text(encoding="utf-8")
    x = re.sub(r"\n<url><loc>https://tripeaseapp.com/(" + "|".join(LANGS) + r")/[^<]*</loc>.*?</url>", "", x, flags=re.S)
    if 'xmlns:xhtml' not in x:
        x = x.replace('xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
                      'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">')
    lastmod = re.search(r"<lastmod>([^<]+)</lastmod>", x)
    lm = f"<lastmod>{lastmod.group(1)}</lastmod>" if lastmod else ""
    alts = lambda page: "".join(f'<xhtml:link rel="alternate" hreflang="{c}" href="{SITE}{u}"/>' for c, u in
                                [("en", url_for(page, None))] + [(LANGS[k][0], url_for(page, k)) for k in langs_for(page)])
    add = "".join(f"\n<url><loc>{SITE}{url_for(page, k)}</loc>{lm}{alts(page)}</url>" for page in ALL_PAGES if indexed(page) for k in langs_for(page))
    x = x.replace("\n</urlset>", add + "\n</urlset>")
    p.write_text(x, encoding="utf-8")


def cmd_build(strict: bool) -> int:
    problems = 0
    for page in ALL_PAGES:
        patch_english(page)
    for page in STATIC_EN:
        patch_english(page, home=True)
    for lang in LANGS:
        f = I18N / f"{lang}.json"
        data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"strings": {}, "js": {}}
        tr = {norm(k): v for k, v in data.get("strings", {}).items()}
        missing: set = set()
        for page in pages_in(lang):
            doc = translate_page(page, lang, tr, missing)
            alternates(doc, page, lang)
            lang_menu(doc, page, lang)
            inject_js(doc, data.get("js", {}))
            out = ROOT / lang / page
            write(doc, out)
            if lang in CHINA_FACING and BLOCKED.search(out.read_text(encoding="utf-8")):
                print(f"ERROR {lang}/{page}: mentions a blocked region term (China-facing marketing rule)")
                problems += 1
        js_missing = [k for k in JS_STRINGS if k not in data.get("js", {})]
        print(f"{lang}: {len(missing)} missing strings, {len(js_missing)} missing script strings")
        if strict and (missing or js_missing):
            problems += 1
            for m in sorted(missing)[:10]:
                print("   missing:", m[:100])
    sitemap()
    return 1 if problems else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "extract":
        cmd_extract(); sys.exit(0)
    sys.exit(cmd_build(strict=(cmd == "check")))
