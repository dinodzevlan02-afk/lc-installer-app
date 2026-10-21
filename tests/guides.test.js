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

test("Kroger 345 flood and wall pack get their guide by part number", () => {
  const fl = G.forPart(PARTS.check("LC-FL-WS-3CCT-Y"));
  assert.strictEqual(fl.url, "/guides/flood/LC-Floodlight-Installation-Guide-Y.pdf");
  assert.strictEqual(fl.bracketName, "Yoke");
  assert.ok(fl.ready);
  assert.strictEqual(G.forPart(PARTS.check("lc-fl-ws-3cct-sf")).url, "/guides/flood/LC-Floodlight-Installation-Guide-SF.pdf");
  assert.strictEqual(G.forPart(PARTS.check("LC-FWP-WS-3CCT")).url, "/guides/wallpack/LC-NightShade-Installation-Guide-FWP.pdf");
  assert.strictEqual(G.forPart(PARTS.check(PARTS.DECIDED["LC-FL32A-40-480-40"])).bracket, "Y");
  assert.strictEqual(G.forPart(PARTS.check("LC-UDL-8-A")), null);
});

test("PART_READY matches the PDFs in app/guides/flood and app/guides/wallpack", () => {
  const root = path.join(__dirname, "..", "app", "guides");
  const files = ["flood", "wallpack"].flatMap(d => fs.existsSync(path.join(root, d))
    ? fs.readdirSync(path.join(root, d)).filter(f => f.endsWith(".pdf")).map(f => d + "/" + f) : []).sort();
  assert.deepStrictEqual(files, G.PART_READY.slice().sort());
  for (const g of Object.values(G.BY_PART)) assert.ok(G.PART_READY.includes(g.file), "guide named but not ready: " + g.file);
  for (const f of files) assert.strictEqual(fs.readFileSync(path.join(root, f)).subarray(0, 5).toString(), "%PDF-");
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
