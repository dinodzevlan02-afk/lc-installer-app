/* Bundled spec sheets (api/shared/specs.js): READY must match app/specs/,
   and every file there must be a PDF. */
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const SPECS = require("../api/shared/specs");

test("READY lists exactly the spec sheets committed in app/specs", () => {
  const dir = path.join(__dirname, "..", "app", "specs");
  const files = fs.existsSync(dir) ? fs.readdirSync(dir).filter(f => f.endsWith(".pdf")).sort() : [];
  assert.deepEqual([...SPECS.READY].sort(), files);
  files.forEach(f => assert.equal(fs.readFileSync(path.join(dir, f)).subarray(0, 5).toString(), "%PDF-", f));
});

test("a part number gets its spec sheet only when the file is there", () => {
  for (const [pn, f] of Object.entries(SPECS.BY_PART)) {
    assert.equal(SPECS.forPart(pn), SPECS.READY.includes(f) ? "/specs/" + f : null, pn);
  }
  assert.equal(SPECS.forPart("LC-NOT-A-PART"), null);
});

test("Kroger 345 flood, wall pack and downlight carry their LC spec sheet", () => {
  assert.equal(SPECS.forPart("LC-FL-WS-3CCT-SF"), "/specs/LC-Floodlight-Selectable.pdf");
  assert.equal(SPECS.forPart("lc-fl-ws-3cct-y"), "/specs/LC-Floodlight-Selectable.pdf");
  assert.equal(SPECS.forPart("LC-FWP-WS-3CCT"), "/specs/LC-Nightshade-Full-Cutoff-Wallpack.pdf");
  assert.equal(SPECS.forPart("LC-UDL-8-A"), "/specs/LC-Universal-Downlight-Series.pdf");
});
