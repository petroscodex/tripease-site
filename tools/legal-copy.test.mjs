import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function walk(dir, out = []) {
  for (const name of fs.readdirSync(dir)) {
    if (name === ".git" || name === "node_modules") continue;
    const full = path.join(dir, name);
    const stat = fs.statSync(full);
    if (stat.isDirectory()) walk(full, out);
    else out.push(full);
  }
  return out;
}

function loadFormatStatusDate() {
  const src = fs.readFileSync(path.join(root, "site.js"), "utf8");
  const start = src.indexOf("function formatStatusDate");
  const end = src.indexOf("/* end formatStatusDate */");
  assert.ok(start >= 0 && end > start, "formatStatusDate is present in site.js");
  const body = src.slice(start, end);
  return new Function(`${body}\nreturn formatStatusDate;`)();
}

const formatStatusDate = loadFormatStatusDate();

test("recorded status dates are real calendar days, and unknown values stay unknown", () => {
  assert.equal(formatStatusDate("2026-11-18"), "2026-11-18");
  assert.equal(formatStatusDate("  2024-02-29 "), "2024-02-29");
  for (const value of [
    null,
    undefined,
    "",
    "   ",
    "[DATE]",
    "[DATES TO CONFIRM]",
    "DATE",
    "unknown",
    "n/a",
    "18 November 2026",
    "2026-02-31",
    "2026-13-01",
    "2026-00-10",
    "2023-02-29",
    "2026-1-1",
    "2026-11-18T00:00:00Z",
    "2026/11/18",
    20261118,
    "Weekly",
  ]) {
    assert.equal(formatStatusDate(value), "", `expected unknown for ${JSON.stringify(value)}`);
  }
});

test("status loader does not invent a date or leave a failed fetch on Loading", () => {
  const src = fs.readFileSync(path.join(root, "site.js"), "utf8");
  assert.match(src, /fetch\("\/data\/status\.json"\)/);
  assert.doesNotMatch(src, /fetch\("data\/status\.json"\)/);
  assert.match(src, /statusUnavailable/);
  assert.match(src, /formatStatusDate\(value\)/);
  assert.doesNotMatch(src, /\.catch\(function\(\)\{\s*\}\)/);
  const data = JSON.parse(fs.readFileSync(path.join(root, "data/status.json"), "utf8"));
  assert.ok(Array.isArray(data.sources) && data.sources.length > 0);
  for (const source of data.sources) {
    assert.equal(source.last, null, source.name);
    assert.match(source.refreshed, /^Aim:/);
  }
  assert.doesNotMatch(JSON.stringify(data), /\[DATE\]/);
});

test("published HTML keeps Plausible and Umami and has no emrldco loader", () => {
  const html = walk(root).filter((file) => file.endsWith(".html"));
  assert.ok(html.length > 100);
  const misses = [];
  for (const file of html) {
    const text = fs.readFileSync(file, "utf8");
    const rel = path.relative(root, file);
    if (text.includes("emrldco.com")) misses.push(`${rel}: emrldco.com`);
    if (!text.includes("https://plausible.io/js/pa-yEmekLdA3Vcj9GWeRgyBh.js")) misses.push(`${rel}: missing Plausible`);
    if (!text.includes("https://cloud.umami.is/script.js")) misses.push(`${rel}: missing Umami`);
    if (!text.includes('data-website-id="6e3b5dc3-0353-4ecc-9f30-58a6b7cd4384"')) misses.push(`${rel}: missing Umami id`);
  }
  assert.deepEqual(misses, []);
});

test("English pages do not keep the absolute claims this fix removes", () => {
  const banned = [
    "collect no personal data",
    "do not track your device location",
    "Nothing personal is sent",
    "zero if you use only free features",
    "Launch price:",
    "at least 24 hours before",
    "Both paid plans include a 14-day free trial",
    "with a 14-day free trial",
    "from our partner SafetyWing",
    "save 50%",
    "[DATE]",
    "emrldco.com",
  ];
  const pages = ["index.html", "help.html", "privacy.html", "terms.html", "site.js"];
  for (const rel of pages) {
    const text = fs.readFileSync(path.join(root, rel), "utf8");
    for (const phrase of banned) {
      assert.equal(text.includes(phrase), false, `${rel} still contains ${phrase}`);
    }
  }
  const terms = fs.readFileSync(path.join(root, "terms.html"), "utf8");
  assert.match(terms, /statutory withdrawal, cooling-off, or other mandatory consumer rights/);
  assert.match(terms, /do not cap that total at zero/);
  assert.match(terms, /cannot be limited or excluded under applicable law/);
  assert.doesNotMatch(terms, /governing law|domicil/i);
  const help = fs.readFileSync(path.join(root, "help.html"), "utf8");
  assert.match(help, /statutory withdrawal, cooling-off, or other mandatory consumer rights/);
  assert.match(help, /does not set a 24-hour deadline/);
  const privacy = fs.readFileSync(path.join(root, "privacy.html"), "utf8");
  assert.match(privacy, /does not claim that no personal data is processed/);
  assert.match(privacy, /section 5\.4a/);
  assert.match(privacy, /https:\/\/plausible\.io\/data-policy/);
  assert.match(privacy, /https:\/\/umami\.is\/privacy/);
  const home = fs.readFileSync(path.join(root, "index.html"), "utf8");
  assert.match(home, /does not promise an Apple trial/);
  assert.match(home, /eligible customers who have never subscribed/);
  assert.match(home, /There is no promise that a launch price lasts/);
  const card = home.slice(home.indexOf("safetywing.com"), home.indexOf('id="get"'));
  assert.match(card, /may earn a commission, at no extra cost to you/);
  assert.match(card, /does not confirm that a commission programme is currently active/);
  assert.doesNotMatch(card, /our partner/i);
});
