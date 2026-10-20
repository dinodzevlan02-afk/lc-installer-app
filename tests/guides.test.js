/* The installation guide PDFs: which bracket gets which file, and the
   READY list in api/shared/guides.js agrees with app/guides/optimus/. */
const test = require("node:test");
const assert = require("node:assert");
const fs = require("fs");
const path = require("path");
const PARTS = require("../api/shared/parts");
const G = require("../api/shared/guides");

const DIR = path.join(__dirname, "..", "app", "guides", "optimus");

test("an Optimus part number gets the guide for its bracket", () => {
  const ss = G.forPart(PARTS.check("LC-SLOT-300W-HV-L5-XX-50-70-T5S-SS-BK"));
  assert.strictEqual(ss.bracket, "SS");
  assert.strictEqual(ss.bracketName, "Straight square arm");
  assert.strictEqual(ss.url, "/guides/optimus/LC-Optimus-Installation-Guide-SS.pdf");
  assert.strictEqual(G.forPart(PARTS.check("LC-SLOT-75W-NV-L5-XX-40-70-T4-U-BK")).bracket, "U");
  for (const code of PARTS.OPTIMUS.bracket) assert.ok(G.BRACKET_NAMES[code], "every order-logic bracket has a guide name: " + code);
});

test("no guide for other families or invalid numbers", () => {
  assert.strictEqual(G.forPart(PARTS.check("LC-WP-40W-50K")), null);
  assert.strictEqual(G.forPart(PARTS.check("LC-SLOT-300W-HV-L5-XX-50-70-T5S-ZZ-BK")), null);
  assert.strictEqual(G.forPart(null), null);
});

test("READY matches the PDFs published in app/guides/optimus", () => {
  const files = fs.existsSync(DIR) ? fs.readdirSync(DIR).filter(f => f.endsWith(".pdf")).sort() : [];
  assert.deepStrictEqual(files, G.READY.map(G.file).sort());
  for (const f of files) assert.strictEqual(fs.readFileSync(path.join(DIR, f)).subarray(0, 5).toString(), "%PDF-");
});
