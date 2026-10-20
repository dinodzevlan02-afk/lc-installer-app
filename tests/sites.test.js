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
  assert.strictEqual(out.rows, 114, "113 audit rows + the 6th flood added on 20203's pole");
  assert.strictEqual(out.heads, 88, "= the A-02's 88 heads");
  assert.strictEqual(out.excluded, 26, "24 existing LED gas canopy heads + 2 heads the design removes");
  const by = Object.fromEntries(out.checks.map(c => [c.tag, c]));
  out.checks.forEach(c => assert.strictEqual(c.pins, c.design, c.tag));
  const ds = out.file.site.datasets[0];
  assert.strictEqual(ds.data.length, 114);
  assert.ok(!JSON.stringify(out.file).includes("sig="), "no signed photo links in the file");
  const fcw1 = Object.keys(ds.solutions).filter(i => ds.solutions[i].tag === "FCW1").map(i => ds.solutions[i].mh).sort();
  assert.deepStrictEqual(fcw1, [12, 15, 15, 15, 15], "FCW1 takes the audit height where the design draws both 12 and 15 ft");
});

test("KR-00345-NV: the 6th flood sits on 20203's pole, opposite it; every flood is on a pole", () => {
  const ds = build(path.join(__dirname, "..", "tools", "sites", "KR-00345-NV")).file.site.datasets[0];
  const row = id => ds.data.find(r => r.id === id);
  const add = row("ADD-FL1-01"), base = row("20203");
  const i = ds.data.indexOf(add);
  assert.strictEqual(ds.solutions[i].tag, "FL1");
  assert.strictEqual(add["pole id"], "G12");
  assert.strictEqual(base["pole id"], "G12");
  assert.match(add.added, /New head/);
  /* opposite: the pole centre (20201 + 20202) is the midpoint of 20203 and the new head */
  const c = { lat: (+row("20201").latitude + +row("20202").latitude) / 2, lng: (+row("20201").longitude + +row("20202").longitude) / 2 };
  assert.ok(Math.abs((+add.latitude + +base.latitude) / 2 - c.lat) < 1e-7 && Math.abs((+add.longitude + +base.longitude) / 2 - c.lng) < 1e-7);
  ds.data.forEach((r, j) => { if (ds.solutions[j] && ds.solutions[j].tag === "FL1") assert.ok(r["pole id"], r.id + " has a pole"); });
  ds.data.forEach((r, j) => { if (ds.solutions[j] && /^(FCW|DL)/.test(ds.solutions[j].tag)) assert.ok(!r["pole id"], r.id + " is on the building, not a pole"); });
});

test("the built file passes the app's own upload check unchanged in counts", () => {
  const out = build(path.join(__dirname, "..", "tools", "sites", "KR-00345-NV"));
  const { meta, site } = FILE.check("KR-00345-NV", out.file, "test");
  assert.strictEqual(meta.fixtures, 88);
  assert.strictEqual(meta.rows, 114);
  assert.strictEqual(meta.name, "Kroger 345 · El Dorado Village");
  assert.strictEqual(Object.keys(site.site.datasets[0].solutions).length, 88);
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
