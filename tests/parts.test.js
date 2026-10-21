/* Unit tests for api/shared/parts.js: UL-listed part numbers checked
   against the Optimus ORDER LOGIC (lc-catalog/lc-skb.js OPTIMUS_OPTS +
   buildSku), and the Walmart A-05 suggestions Dino decided 2026-10-20. */
const test = require("node:test");
const assert = require("node:assert/strict");
const PARTS = require("../api/shared/parts");

test("a valid Optimus part number passes and is explained", () => {
  const c = PARTS.check("lc-slot-300w-hv-l5-xx-50-70-t5s-ss-bk");
  assert.equal(c.ok, true);
  assert.equal(c.pn, "LC-SLOT-300W-HV-L5-XX-50-70-T5S-SS-BK", "upper-cased");
  assert.equal(c.checked, true);
  assert.equal(c.short, "Optimus 300W \u00b7 T5S");
  assert.deepEqual(c.parts, { watts: 300, volt: "200-480V", sensor: "No sensor", cct: "5000K", cri: "CRI 70",
    optic: "Type V square", bracket: "Straight square arm", color: "Black",
    means: "300W \u00b7 200-480V \u00b7 5000K \u00b7 CRI 70 \u00b7 Type V square \u00b7 Straight square arm bracket \u00b7 Black \u00b7 No sensor" });
});

test("a plausible-looking but wrong Optimus number is refused", () => {
  assert.equal(PARTS.check("LC-SLOT-XL-XL1-HV-50-70-TY5SW").ok, false, "the design label itself is not a part number");
  assert.match(PARTS.check("LC-SLOT-300W-HV-L5-XX-50-70-T5SW-SS-BK").error, /not a valid dist/, "TY5SW wide optic has no order code");
  assert.match(PARTS.check("LC-SLOT-310W-HV-L5-XX-50-70-T5S-SS-BK").error, /not a valid watt/);
  assert.match(PARTS.check("LC-SLOT-300W-HV-L3-XX-50-70-T5S-SS-BK").error, /L5/);
  assert.match(PARTS.check("LC-SLOT-300-HV-L5-XX-50-70-T5S-SS-BK").error, /end in W/);
  assert.match(PARTS.check("LC-SLOT-300W-HV-L5-50-70-T5S-SS-BK").error, /11 segments/);
});

test("a Prime Wallpack part number is checked against its order logic", () => {
  const c = PARTS.check("lc-wp-40w-l-40k");
  assert.equal(c.ok, true);
  assert.equal(c.pn, "LC-WP-40W-L-40K");
  assert.equal(c.checked, true);
  assert.equal(c.short, "Prime Wallpack 40W \u00b7 Low output");
  assert.equal(c.parts.means, "40W \u00b7 Low output \u00b7 4000K \u00b7 No accessory");
  assert.equal(PARTS.check("LC-WP-80W-H-40K-MS").parts.accessory, "Microwave sensor");
  assert.match(PARTS.check("LC-WP-45W-H-40K").error, /not a valid Prime Wallpack watt/, "the design's 45W does not exist");
  assert.match(PARTS.check("LC-WP-40W-H-40K-70").error, /accessory/, "CRI is not part of the LC code");
  assert.match(PARTS.check("LC-WP-40W-50K").error, /LC-WP-\{watt\}W/);
});

test("other LED Connection part numbers are accepted but marked unchecked", () => {
  const c = PARTS.check("LC-FL-170-HV-50");
  assert.equal(c.ok, true);
  assert.equal(c.checked, false);
  assert.equal(PARTS.check("AOK-300WoT-HV-BK-50-70-T542-E").ok, false, "a supplier code is not an LC part number");
  assert.equal(PARTS.check("").ok, false);
});

test("every decided part number is a valid LC part number (Walmart A-05, Kroger 345 A-02)", () => {
  const want = {
    "LC-SLOT-S-S1-NV-40-70-TY4W-W-N": "LC-SLOT-75W-NV-L5-XX-40-70-T4-U-BK",
    "LC-SLOT-S-S1-NV-40-70-TY4W-W": "LC-SLOT-75W-NV-L5-XX-40-70-T4-U-BK",
    "LC-SLOT-145-HV-L5-50-TY03": "LC-SLOT-145W-HV-L5-XX-50-70-T3-U-BK",
    "LC-SLOT-L-L3-HV-50-70-TY5SW": "LC-SLOT-230W-HV-L5-XX-50-70-T5S-SS-BK",
    "LC-SLOT-XL-XL1-HV-50-70-TY5SW": "LC-SLOT-300W-HV-L5-XX-50-70-T5S-SS-BK",
    "LC-SLOT-XL-XL2-HV-30-70-TY5S": "LC-SLOT-420W-HV-L5-XX-30-70-T5S-SS-BK",
    "FCW-45-NV-740-CT": "LC-WP-40W-H-40K",
    "FCW-20-NV-740-CT": "LC-WP-40W-L-40K",
    "LC-SLOT-L-L1-480-40-70-TY5SW": "LC-SLOT-230W-HV-L5-XX-40-80-T5S-SS-BR",
    "LC-SLOT-L-S1-480-40-70-TY4W": "LC-SLOT-230W-HV-L5-XX-40-80-T4-SS-BR",
    "LC-SLOT-L-S1-480-40-70-TY4W-HS": "LC-SLOT-230W-HV-L5-XX-40-80-T4-SS-BR",
    "FCW-20-740-277-CT": "LC-FWP-WS-3CCT",
    "FCW-45-740-277-CT": "LC-FWP-WS-3CCT",
    "LC-FL32A-40-480-40": "LC-FL-WS-3CCT-SF",
    "LC-UDL-10-16W-277-40-GR": "LC-UDL-8-A"
  };
  assert.deepEqual(PARTS.DECIDED, want);
  for (const pn of Object.values(PARTS.DECIDED)) assert.equal(PARTS.check(pn).ok, true, pn);
});

test("Kroger 345: every design label has a part number and a set-up line; the Optimus ones are checked", () => {
  const tags = require("../tools/sites/KR-00345-NV/project.json").design.tags;
  for (const [tag, d] of Object.entries(tags)) {
    const pn = PARTS.DECIDED[d.label];
    assert.ok(pn, tag + " has a decided part number");
    assert.ok(PARTS.SETUP[d.label], tag + " has a set-up line");
    const c = PARTS.check(pn);
    assert.equal(c.checked, d.fam === "Optimus", tag + (d.fam === "Optimus" ? " checked against the order logic" : " accepted, not checked"));
  }
  const s03 = PARTS.check(PARTS.DECIDED["LC-SLOT-L-L1-480-40-70-TY5SW"]);
  assert.equal(s03.parts.means, "230W \u00b7 200-480V \u00b7 4000K \u00b7 CRI 80 \u00b7 Type V square \u00b7 Straight square arm bracket \u00b7 Bronze \u00b7 No sensor");
  assert.match(PARTS.SETUP["LC-SLOT-L-S1-480-40-70-TY4W-HS"], /75W.*shield/);
});
