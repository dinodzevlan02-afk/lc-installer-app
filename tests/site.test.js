/* Unit tests for api/shared/site.js - the reader that turns a customer-portal
   site into an installer's job: product counts (the material check), pins,
   tags, and what may leave the server.

     node --test tests/            (npm test runs this and the API checks)

   Built-in node:test, no packages. The names below are the portal's own
   examples (lc-customer-portal/portal.html cpShortProduct), so if the two
   ever disagree on a product name, this fails. The site is the SYNTHETIC
   TEST-SITE-01 in tests/fixtures: pipeline checks, never results. */
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("path");

process.env.INSTALLER_PORTAL_LOCAL_STORE = path.join(__dirname, "fixtures", "portal");
/* The app's own store is read first (sites uploaded here): an empty one, so
   these tests read the portal's site. */
process.env.INSTALLER_LOCAL_STORE = require("fs").mkdtempSync(path.join(require("os").tmpdir(), "lci-site-test-"));
process.env.INSTALLER_CATALOG_FILE = path.join(__dirname, "fixtures", "catalog-data.json");
const SITE = require("../api/shared/site");

test("short product names match the customer portal", () => {
  /* Watts in the SKU. The portal's comment above cpShortProduct says this
     gives "Optimus 230W · T5S", but its code reads the L5 segment as a head
     size (the S/L/XL rule added for Walmart), so the portal shows
     "Optimus L5 230W · T5S". This app matches what the portal SHOWS; open
     question for Dino (CLAUDE.md, open items): is L5 ever a head size? */
  assert.equal(SITE.shortProduct({ fam: "Optimus", lc_sku: "LC-SLOT-230W-NV-L5-XX-40-80-T5S-F-BR" }), "Optimus L5 230W · T5S");
  assert.equal(SITE.shortProduct({ fam: "Optimus", lc_sku: "LC-SLOT-230W-NV-XX-40-80-T5S-F-BR" }), "Optimus 230W · T5S");
  /* Optimus SKUs that carry the head size, watts from the solution. */
  assert.equal(SITE.shortProduct({ fam: "Optimus", lc_sku: "LC-SLOT-XL-XL1-HV-50-70-TY5SW", watt: 230 }), "Optimus XL1 230W · TY5SW");
  /* TYPE3 is written T3. */
  assert.equal(SITE.shortProduct({ fam: "Flood", lc_sku: "FL-150W-TYPE3" }), "Flood 150W · T3");
  /* Nothing to shorten: the fallback. */
  assert.equal(SITE.shortProduct(null, "AL1 · AreaLight"), "AL1 · AreaLight");
});

test("fixture id and existing watts follow the portal", () => {
  assert.equal(SITE.fixtureId({ id: " 6177 " }, 3), "6177");
  assert.equal(SITE.fixtureId({}, 3), "row-3");
  assert.equal(SITE.existingWatts({ "system wattage": "458", wattage: "400" }), 458, "system wattage (lamp + ballast) wins");
  assert.equal(SITE.existingWatts({ wattage: "32", "number of lamps": "2" }), 64);
  assert.equal(SITE.existingWatts({}), null);
});

test("pin ids are stable for the same dataset and fixture", () => {
  assert.equal(SITE.pinKey("ds-1", "6177"), SITE.pinKey("ds-1", "6177"));
  assert.notEqual(SITE.pinKey("ds-1", "6177"), SITE.pinKey("ds-2", "6177"));
  assert.match(SITE.pinKey("ds-1", "6177"), /^[a-f0-9]{20}$/);
});

test("the material list counts heads per product, leaving excluded heads out", async () => {
  const s = await SITE.loadSite("TEST-SITE-01");
  assert.deepEqual(s.bom.map(b => [b.name, b.qty]), [["Optimus XL1 230W · TY5SW", 6], ["Prime Wallpack 40W", 2]]);
  assert.equal(s.pins.length, 9, "every audit row is a pin");
  assert.equal(s.pins.filter(p => p.off).length, 1);
  assert.equal(s.bom.reduce((n, b) => n + b.qty, 0), s.pins.filter(p => !p.off && p.product).length,
    "material total = heads to install");
  assert.deepEqual(s.tags, [{ tag: "S07", count: 4 }, { tag: "S08", count: 2 }, { tag: "W1", count: 2 }]);
});

test("pins carry the design's tag (luminaire schedule), the audit's tag kept beside it", async () => {
  const s = await SITE.loadSite("TEST-SITE-01");
  const p = s.pins.find(x => x.fid === "T-000");
  assert.equal(p.tag, "S07", "design tag (sol.tag) wins");
  assert.equal(p.auditTag, "AL1", "audit tag kept for reference");
  const off = s.pins.find(x => x.off);
  assert.equal(off.tag, "FCWP1", "a head with no design falls back to the audit tag");
  const opt = s.bom.find(b => b.fam === "Optimus");
  assert.deepEqual(opt.tags, ["S07", "S08"]);
  assert.deepEqual(opt.tagCounts, { S07: 4, S08: 2 }, "one product serving two design tags, heads per tag");
});

test("a position corrected in the portal (MOVE PINS) wins", async () => {
  const s = await SITE.loadSite("TEST-SITE-01");
  const p = s.pins.find(x => x.fid === "T-007");
  assert.ok(Math.abs(p.lng - (-115.0300 + 0.0008)) < 1e-9);
});

test("nothing internal leaves the reader", async () => {
  const s = await SITE.loadSite("TEST-SITE-01");
  const FORBIDDEN = ["costPrice", "sellPrice", "landedCost", "margin", "vendor", "vn_sku", "skbSnapshot", "designNote", "notes", "netsuite"];
  const keys = new Set();
  (function walk(v) {
    if (Array.isArray(v)) v.forEach(walk);
    else if (v && typeof v === "object") Object.entries(v).forEach(([k, x]) => { keys.add(k); walk(x); });
  })(s);
  for (const k of FORBIDDEN) assert.ok(!keys.has(k), "field " + k + " must not leave site.js");
  assert.ok(!JSON.stringify(s).includes("SECRET VENDOR"));
  assert.ok(!JSON.stringify(s).includes("INTERNAL AUDIT NOTE"));
});

test("a project the portal does not have reads as null", async () => {
  assert.equal(await SITE.loadSite("NO-SUCH-SITE"), null);
});
