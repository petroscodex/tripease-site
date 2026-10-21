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
* China-facing rule: the Simplified Chinese pages must not mention Taiwan (build fails if they do).
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
PAGES = ["index.html"]
LANGS = {  # url folder: (BCP-47 code, menu label, html lang attribute)
    "zh-hans": ("zh-Hans", "简体中文", "zh-Hans"),
    "zh-hant": ("zh-Hant", "繁體中文", "zh-Hant"),
    "ja": ("ja", "日本語", "ja"),
    "ko": ("ko", "한국어", "ko"),
    "th": ("th", "ไทย", "th"),
    "de": ("de", "Deutsch", "de"),
    "fr": ("fr", "Français", "fr"),
    "es": ("es", "Español", "es"),
}
CHINA_FACING = {"zh-hans"}
TAIWAN = re.compile(r"Taiwan|台湾|臺灣|台灣", re.I)
# A segment is the innermost block holding text; links inside it stay part of the sentence.
BLOCK = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "dt", "dd", "td", "th", "caption", "summary",
         "label", "legend", "button", "figcaption", "title", "option"}
SEG = BLOCK | {"a"}  # a link is its own segment only when it isn't inside a block
INLINE = {"a", "b", "strong", "em", "i", "span", "small", "br", "code", "abbr"}
ATTRS = ("alt", "title", "aria-label")
META = {("name", "description"), ("property", "og:title"), ("property", "og:description"),
        ("property", "og:image:alt"), ("name", "twitter:title"), ("name", "twitter:description")}
JSONLD_KEYS = {"alternateName", "description", "slogan", "featureList", "name", "text"}
HAS_WORDS = re.compile(r"[A-Za-z]")
BRAND = {"TripEase", "Petros Codex", "EN"}
# Same in every language: airport codes, plug types, handles, names of publications and datasets.
SOCIAL = r"(?:TikTok|Instagram|YouTube|X)"
KEEP = re.compile(r"^(?:[A-Z]{3}(?: · [A-Z]{3})*|" + SOCIAL + r"(?: · " + SOCIAL + r")+|[A-N](?:, [A-N])* · \d+ V|(?:TikTok|Instagram|YouTube|X)(?: @\S+)?"
                  r"|Bangkok Post|Khaosod English|TravelRequirements\.info Entry Requirements Dataset|SIL Open Font License)$")
LANG_UI = ("lang", "foot-langs")  # the language menu itself is never translated


def norm(s: str) -> str:
    return " ".join(s.split())


def skip(text: str) -> bool:
    return text in BRAND or bool(KEEP.match(text)) or not HAS_WORDS.search(text)


def in_lang_ui(el) -> bool:
    return any(LANG_UI[0] in (p.get("class") or []) or LANG_UI[1] in (p.get("class") or [])
               for p in [el, *el.parents] if getattr(p, "get", None))


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
        return o.get("@type") == "Question"
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
        out += [norm(el[a]) for a in ATTRS if el.get(a) and not skip(norm(el[a]))]
        if el.name == "meta" and any(el.get(k) == v for k, v in META) and el.get("content"):
            out.append(norm(el["content"]))
    for s in doc.find_all("script", type="application/ld+json"):
        out += jsonld_strings(json.loads(s.string), [])
    return list(dict.fromkeys(out))


JS_STRINGS = json.loads((Path(__file__).parent / "js_strings.json").read_text(encoding="utf-8"))


def cmd_extract() -> None:
    src = {}
    for page in PAGES:
        for s in strings(soup(ROOT / page)):
            src.setdefault(s, []).append(page)
    I18N.mkdir(exist_ok=True)
    (I18N / "source.json").write_text(json.dumps({"_note": "Generated by tools/i18n/build.py extract. "
        "Keys are the English strings; translate them in i18n/<lang>.json.", "strings": src, "js": JS_STRINGS},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"extract: {len(src)} strings from {len(PAGES)} page(s), {len(JS_STRINGS)} script strings")


def url_for(page: str, lang: str | None) -> str:
    path = "/" if page == "index.html" else f"/{page}"
    return path if not lang else f"/{lang}{path}"


def plain(html: str) -> str:
    return norm(BeautifulSoup(html, "html.parser").get_text())


def _names():
    return [(None, "en", "English")] + [(k, v[0], v[1]) for k, v in LANGS.items()]


def _cur(k, cur) -> str:
    return ' aria-current="true"' if k == cur else ""


def menu_html(page: str, cur: str | None) -> str:
    cur_label = "EN" if not cur else LANGS[cur][1]
    items = "".join('<li><a href="%s" hreflang="%s" lang="%s"%s>%s</a></li>' % (url_for(page, k), code, code, _cur(k, cur), label)
                    for k, code, label in _names())
    return '<details class="lang"><summary aria-label="Language">' + cur_label + "</summary><ul>" + items + "</ul></details>"


def foot_html(page: str, cur: str | None) -> str:
    links = " · ".join('<a href="%s" hreflang="%s" lang="%s"%s>%s</a>' % (url_for(page, k), code, code, _cur(k, cur), label)
                        for k, code, label in _names())
    return '<nav class="foot-langs" aria-label="Language">' + links + "</nav>"


def alt_html(page: str) -> str:
    links = [("en", url_for(page, None))] + [(v[0], url_for(page, k)) for k, v in LANGS.items()] + [("x-default", url_for(page, None))]
    return "\n".join(f'  <link rel="alternate" hreflang="{c}" href="{SITE}{u}" />' for c, u in links)


def patch_english(page: str) -> None:
    """The English page is Zan's hand-written source: change only the language links, the header menu
    and the footer list, as text, so the rest of the file stays byte-for-byte as she wrote it."""
    path = ROOT / page
    x = path.read_text(encoding="utf-8")
    x = re.sub(r'\n[ \t]*<link rel="alternate" hreflang="[^"]*" href="[^"]*" ?/?>', "", x)
    x = re.sub(r'(<link rel="canonical"[^>]*>)', lambda m: m.group(1) + "\n" + alt_html(page), x, count=1)
    x = re.sub(r'<button class="lang"[^>]*>.*?</button>|<details class="lang">.*?</details>',
               lambda m: menu_html(page, None), x, count=1, flags=re.S)
    x = re.sub(r'<nav class="foot-langs".*?</nav>\n?[ \t]*', "", x, flags=re.S)
    x = re.sub(r'([ \t]*)(<div class="legal-lines">)', lambda m: m.group(1) + foot_html(page, None) + "\n" + m.group(1) + m.group(2), x, count=1)
    path.write_text(x, encoding="utf-8")


def lang_menu(doc: BeautifulSoup, page: str, cur: str | None) -> None:
    """Header menu (desktop) and footer list (every screen size) in a generated page."""
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
    links = [("en", url_for(page, None))] + [(v[0], url_for(page, k)) for k, v in LANGS.items()] + [("x-default", url_for(page, None))]
    for code, path in links:
        tag = doc.new_tag("link", rel="alternate", hreflang=code, href=SITE + path)
        anchor.insert_after(tag); anchor.insert_after("\n  "); anchor = tag
    canon["href"] = SITE + url_for(page, cur)


def fix_url(u: str) -> str:
    if not u or re.match(r"^([a-z]+:|/|#|\?)", u):
        return u
    return "/" + u


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
            if el.get(a) and not skip(norm(el[a])) and not in_lang_ui(el):
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
        for p in PAGES:
            if path in {url_for(p, None), "/" + p} or (p == "index.html" and path == ""):
                if path == "" and frag is not None:
                    break  # same-page anchor (#pricing): already fine
                a["href"] = url_for(p, lang) + (f"#{frag}" if frag is not None else "")
                break
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
                    elif k == "url" and v == SITE + "/":
                        o[k] = SITE + url_for(page, lang)
                    else:
                        walk(v)
            elif isinstance(o, list):
                for x in o:
                    walk(x)
        walk(data)
        s.string = json.dumps(data, ensure_ascii=False)
    doc.html["lang"] = html_lang
    og = doc.find("meta", property="og:url")
    if og:
        og["content"] = SITE + url_for(page, lang)
    doc.head.append(doc.new_tag("meta", property="og:locale", content=code.replace("-", "_")))
    return doc


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
                                [("en", url_for(page, None))] + [(v[0], url_for(page, k)) for k, v in LANGS.items()])
    add = "".join(f"\n<url><loc>{SITE}{url_for(page, k)}</loc>{lm}{alts(page)}</url>" for page in PAGES for k in LANGS)
    x = x.replace("\n</urlset>", add + "\n</urlset>")
    p.write_text(x, encoding="utf-8")


def cmd_build(strict: bool) -> int:
    problems = 0
    for page in PAGES:
        patch_english(page)
    for lang in LANGS:
        f = I18N / f"{lang}.json"
        data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"strings": {}, "js": {}}
        tr = {norm(k): v for k, v in data.get("strings", {}).items()}
        missing: set = set()
        for page in PAGES:
            doc = translate_page(page, lang, tr, missing)
            alternates(doc, page, lang)
            lang_menu(doc, page, lang)
            inject_js(doc, data.get("js", {}))
            out = ROOT / lang / page
            write(doc, out)
            if lang in CHINA_FACING and TAIWAN.search(out.read_text(encoding="utf-8")):
                print(f"ERROR {lang}/{page}: mentions Taiwan (China-facing marketing rule)")
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
