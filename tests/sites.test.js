/* Site files built for the installer app (tools/sites/build-site.js).
   KR-00345-NV is a REAL site (Kroger 345, El Dorado Village): its inputs
   are the LED Audit app export and the Field Survey mapping in
   tools/sites/KR-00345-NV, and the counts below are checked against the
   approved A-02's luminaire schedule. */
const test = require("node:test");
const assert = require("node:assert");
const path = require("path");
const { build, parseCsv } = require("../tools/sites/build-site");
const FILE = require("../api/shared/sitefile");

test("CSV reader: quoted fields, doubled quotes, CRLF, BOM", () => {
  const rows = parseCsv('﻿a,b,c\r\n1,"2"" pipe","x,y"\r\n', ",");
  assert.deepStrictEqual(rows, [{ a: "1", b: '2" pipe', c: "x,y" }]);
});

test("KR-00345-NV: every audit row placed, heads per tag as the A-02 schedule", () => {
  const out = build(path.join(__dirname, "..", "tools", "sites", "KR-00345-NV"));
  assert.deepStrictEqual(out.errors, []);
  assert.strictEqual(out.rows, 113);
  assert.strictEqual(out.heads, 87);
  assert.strictEqual(out.excluded, 26, "24 existing LED gas canopy heads + 2 heads the design removes");
  const by = Object.fromEntries(out.checks.map(c => [c.tag, c]));
  ["S03", "S02-HS", "S01", "FCW2", "FCW1", "DL1-GR"].forEach(t => assert.strictEqual(by[t].pins, by[t].design, t));
  assert.deepStrictEqual([by.FL1.design, by.FL1.pins], [6, 5], "one design flood has no audit pin (open with Dino)");
  const ds = out.file.site.datasets[0];
  assert.strictEqual(ds.data.length, 113);
  assert.ok(!JSON.stringify(out.file).includes("sig="), "no signed photo links in the file");
  const fcw1 = Object.keys(ds.solutions).filter(i => ds.solutions[i].tag === "FCW1").map(i => ds.solutions[i].mh).sort();
  assert.deepStrictEqual(fcw1, [12, 15, 15, 15, 15], "FCW1 takes the audit height where the design draws both 12 and 15 ft");
});

test("the built file passes the app's own upload check unchanged in counts", () => {
  const out = build(path.join(__dirname, "..", "tools", "sites", "KR-00345-NV"));
  const { meta, site } = FILE.check("KR-00345-NV", out.file, "test");
  assert.strictEqual(meta.fixtures, 87);
  assert.strictEqual(meta.rows, 113);
  assert.strictEqual(meta.name, "Kroger 345 · El Dorado Village");
  assert.strictEqual(Object.keys(site.site.datasets[0].solutions).length, 87);
});

test("upload check: keeps only the solution fields an installer may see", () => {
  const body = { format: "lc-site", version: 1, project: { id: "T-1", name: "T" },
    site: { datasets: [{ id: "d1", data: [{ id: "1", images: "https://x/?sig=1", schedule: "A" }],
      solutions: { 0: { fam: "Optimus", lc_sku: "X", tag: "S1", costPrice: 9, vendor: "SECRET", skbSnapshot: { a: 1 } } } }] } };
  const { site } = FILE.check("T-1", body, "t");
  const ds = site.site.datasets[0];
  assert.deepStrictEqual(ds.solutions["0"], { fam: "Optimus", lc_sku: "X", tag: "S1" });
  assert.ok(!("images" in ds.data[0]));
  assert.throws(() => FILE.check("T-2", body, "t"), /not "T-2"/);
  assert.throws(() => FILE.check("T-1", Object.assign({}, body, { site: { datasets: [{ id: "d1", data: [{}], solutions: { 5: {} } }] } }), "t"), /row 5 does not exist/);
  assert.throws(() => FILE.check("T-1", { format: "x" }, "t"), /Not a site file/);
});
