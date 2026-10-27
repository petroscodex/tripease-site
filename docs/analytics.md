# Website analytics (Plausible and Umami)

tripeaseapp.com currently runs **two** cookieless analytics tools side by side: [Plausible Analytics](https://plausible.io) and [Umami](https://umami.is) (Cloud). Peter is evaluating both and will drop one later. Both count visits and show which links and campaigns (UTM tags) brought them. Neither sets cookies, so no consent banner is needed. The privacy policy says so in section 5.4a, naming both tools.

## The tags

### Plausible

```html
<!-- Privacy-friendly analytics by Plausible -->
<script async src="https://plausible.io/js/pa-zVuUTJYzhLW005VfdKnnw.js"></script>
<script>
  window.plausible=window.plausible||function(){(plausible.q=plausible.q||[]).push(arguments)},plausible.init=plausible.init||function(i){plausible.o=i||{}};
  plausible.init()
</script>
```

This is the site-specific snippet from the tripeaseapp.com site in Peter's Plausible account (script id `pa-zVuUTJYzhLW005VfdKnnw`). It replaces the old generic tag (`<script defer data-domain="tripeaseapp.com" src="https://plausible.io/js/script.outbound-links.js">`), which is gone from every page. Do not add it back.

It sits at the end of `<head>` on **every** HTML page (all 346: the English pages and every generated `/<lang>/` page). Outbound link tracking and the other features are switched on or off in the Plausible site settings (Site settings > Tracking), not in the script, so changing them needs no code change. Outbound link clicks (Travelpayouts, SafetyWing and so on) show up as the `Outbound Link: Click` goal once that setting is on.

* **English pages** carry the block in their own source files. This includes `privacy.html`, `terms.html`, `press.html` and `404.html`, which do not load `/site.js`, so the block is inline in their head and not injected by JavaScript.
* **Translated pages** get the block from `python3 tools/i18n/build.py build`, which copies the English head. The build re-serialises the HTML, so on those pages `async` is written as `async=""`. That is the same thing. After changing an English page, run the build and commit the result.
* **New pages** need the same block in their `<head>`. Check with `git ls-files '*.html' | xargs grep -L pa-zVuUTJYzhLW005VfdKnnw` (it should print nothing).
* The `impact-site-verification` meta tag and any other verification tags are separate and untouched.

### Umami (Cloud)

```html
<script defer src="https://cloud.umami.is/script.js" data-website-id="6e3b5dc3-0353-4ecc-9f30-58a6b7cd4384"></script>
```

This is the Umami Cloud script from Peter's Umami account, with website id `6e3b5dc3-0353-4ecc-9f30-58a6b7cd4384`. It sits directly after the Plausible block at the end of `<head>` on every page (346). On the generated language pages `defer` is written as `defer=""`, which is the same thing. Umami records UTM parameters (`utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`) automatically from the landing URL; see the UTM insight in the Umami dashboard ([docs](https://umami.is/docs/utm)). Check a new page with `git ls-files '*.html' | xargs grep -L 6e3b5dc3-0353-4ecc-9f30-58a6b7cd4384` (it should print nothing).

### Dropping one tool later

Removing a tool = delete its one block (Plausible: the comment plus two `<script>` elements; Umami: the one `<script>` line) from the English pages, then run `python3 tools/i18n/build.py build` and commit the result. If Plausible is dropped, also update `docs/analytics.md` and privacy section 5.4a to say so. If Umami is dropped, reword 5.4a the same way.

## Setup Peter must do (one time)

The tag only reports once the site exists in Plausible.

1. Sign in to [plausible.io](https://plausible.io) with your own account (about US$9 a month; there is a free trial).
2. Add a site with the domain **`tripeaseapp.com`** (no `www.`, no `https://`). Done: the snippet above came from that site.
3. Turn "Outbound links" on under Site settings > Tracking if it is not already.
4. Open the site once and use Plausible's "Verify installation" check.

## UTM campaigns

Plausible (and Umami, see above) records `utm_source`, `utm_medium`, `utm_campaign`, `utm_content` and `utm_term` from the landing URL with no extra setup (also `ref` and `source`). They appear in the **Campaigns** tab. Notes:

* Attribution applies to the first pageview of a session (30 minutes). To test, use a device that has not visited the site in the last 30 minutes.
* Redirects must keep the query string. On this site nothing strips it: no page redirects with JavaScript or a meta refresh, and GitHub Pages keeps the query string when it redirects `www.` to the bare domain and when it adds a trailing slash. Unknown paths return `404.html` at the same address, so tagged links to them still get counted.
* Links in posts should point at real pages, for example `https://tripeaseapp.com/?utm_source=tiktok&utm_medium=social&utm_campaign=teaser&utm_content=v1`.

## Why Plausible (and Umami as the alternative)

* UTM and campaign reports are built in.
* No cookies and no personal data, so no consent banner.
* Simplest setup: one script tag, no server to run.
* Hosted in the EU.

[Umami](https://umami.is) is the alternative if a free option is wanted: it is open source and can be self-hosted (or used in its cloud), and it also reads UTM tags. Self-hosting means you run and update it yourself; the Cloud version used here has a free tier. Both are installed for now while Peter compares them.
