/* LC Installer App - UL-listed part numbers for what is installed.

   A photometric design labels its luminaires its own way (A-05:
   "LC-SLOT-XL-XL1-HV-50-70-TY5SW", by head size and IES file). What is
   ordered, shipped and installed is the UL-listed LED Connection part
   number from the spec sheet's ORDER LOGIC (Dino, 2026-10-20: "change all
   the codes that are on the design ... apply these codes first"). A job
   keeps its own table, design label -> part number, edited by LED
   Connection and checked here before it is saved.

   Optimus order logic, kept in step with lc-catalog/lc-skb.js OPTIMUS_OPTS
   and buildSku (11 segments):
     LC-SLOT-{watt}W-{volt}-L5-{sensor}-{cct}-{cri}-{dist}-{bracket}-{color}
   Prime Wallpack order logic, kept in step with lc-skb.js WP_OPTS and its
   buildSku (CRI is not in the LC code; the accessory is left off for none):
     LC-WP-{watt}W-{H|L}-{cct}K[-{accessory}]
   A part number that looks like one of these must be a valid one: the
   catalog rule is that a plausible-looking guessed part number is worse
   than none. Other families are accepted as LC part numbers and shown as
   "not checked against an order logic here". */

const OPTIMUS = {
  watt: ["75", "115", "145", "180", "200", "230", "300", "360", "420"],
  volt: ["NV", "HV", "LVDC"],
  sensor: ["XX", "SN20", "SN40", "3PC", "7PC", "NET"],
  cct: ["30", "40", "50"],
  cri: ["70", "80", "90", "CS"],
  dist: ["T3", "T4", "T4M", "T5", "T5S"],
  bracket: ["F", "SS", "SR", "R", "U", "T"],
  color: ["BK", "BR", "WH", "CS"]
};
/* What an installer reads for each code (spec-sheet labels). The supplier's
   own bracket letters are deliberately not here. */
const LABELS = {
  volt: { NV: "120-277V", HV: "200-480V", LVDC: "Class 2 remote power supply" },
  sensor: { XX: "No sensor", SN20: "Motion & daylight sensor (20' lens)", SN40: "Motion & daylight sensor (40' lens)", "3PC": "3-pin photocell", "7PC": "7-pin NEMA photocell", NET: "Addressable network control" },
  cct: { 30: "3000K", 40: "4000K", 50: "5000K" },
  cri: { 70: "CRI 70", 80: "CRI 80", 90: "CRI 90", CS: "Custom CRI" },
  dist: { T3: "Type III", T4: "Type IV", T4M: "Type IV medium", T5: "Type V round", T5S: "Type V square" },
  bracket: { F: "Slipfitter", SS: "Straight square arm", SR: "Straight round arm", R: "Adjustable straight arm", U: "Yoke", T: "Trunnion" },
  color: { BK: "Black", BR: "Bronze", WH: "White", CS: "Custom color" }
};

const WALLPACK = {
  watt: ["28", "40", "60", "80", "100", "120"],
  effect: ["H", "L"],
  cct: ["35K", "40K", "50K", "57K", "65K"],
  acc: ["MS", "EM", "EMS", "PT", "PM"]
};
const WP_LABELS = {
  effect: { H: "Standard output", L: "Low output" },
  cct: { "35K": "3500K", "40K": "4000K", "50K": "5000K", "57K": "5700K", "65K": "6500K" },
  acc: { "": "No accessory", MS: "Microwave sensor", EM: "Emergency pack", EMS: "Emergency pack + sensor", PT: "Photocell", PM: "Photocell + microwave sensor" }
};

const RE_GENERIC = /^LC-[A-Z0-9]+(-[A-Z0-9.]+){1,15}$/;

/* -> { ok, pn, family, checked, error?, parts? } */
function check(raw) {
  const pn = String(raw == null ? "" : raw).trim().toUpperCase();
  if (!pn) return { ok: false, pn, error: "empty" };
  if (/^LC-SLOT\b/.test(pn)) {
    const s = pn.split("-");
    if (s.length !== 11) return { ok: false, pn, error: "An Optimus part number has 11 segments: LC-SLOT-{watt}W-{volt}-L5-{sensor}-{CCT}-{CRI}-{optic}-{bracket}-{color}." };
    const [, , w, volt, led, sensor, cct, cri, dist, bracket, color] = s;
    const seg = { watt: w.replace(/W$/, ""), volt, sensor, cct, cri, dist, bracket, color };
    if (!/W$/.test(w)) return { ok: false, pn, error: "Watt segment must end in W, e.g. 300W." };
    if (led !== "L5") return { ok: false, pn, error: "The LED segment is always L5." };
    for (const [k, v] of Object.entries(seg)) {
      if (!OPTIMUS[k].includes(v)) return { ok: false, pn, error: "\"" + v + "\" is not a valid " + k + " code (" + OPTIMUS[k].join(", ") + ")." };
    }
    const parts = { watts: Number(seg.watt), volt: LABELS.volt[volt], sensor: LABELS.sensor[sensor], cct: LABELS.cct[cct], cri: LABELS.cri[cri],
      optic: LABELS.dist[dist], bracket: LABELS.bracket[bracket], color: LABELS.color[color] };
    parts.means = [parts.watts + "W", parts.volt, parts.cct, parts.cri, parts.optic, parts.bracket + " bracket", parts.color, parts.sensor].join(" \u00b7 ");
    return { ok: true, pn, family: "Optimus", checked: true, short: "Optimus " + seg.watt + "W \u00b7 " + dist, codes: seg, parts };
  }
  if (/^LC-WP\b/.test(pn)) {
    const s = pn.split("-");
    if (s.length !== 5 && s.length !== 6) return { ok: false, pn, error: "A Prime Wallpack part number reads LC-WP-{watt}W-{H|L}-{CCT}K, with an accessory code at the end if it has one." };
    const [, , w, effect, cct, acc = ""] = s;
    if (!/W$/.test(w)) return { ok: false, pn, error: "Watt segment must end in W, e.g. 40W." };
    const seg = { watt: w.replace(/W$/, ""), effect, cct };
    for (const [k, v] of Object.entries(seg)) {
      if (!WALLPACK[k].includes(v)) return { ok: false, pn, error: "\"" + v + "\" is not a valid Prime Wallpack " + k + " code (" + WALLPACK[k].join(", ") + ")." };
    }
    if (acc && !WALLPACK.acc.includes(acc)) return { ok: false, pn, error: "\"" + acc + "\" is not a valid Prime Wallpack accessory code (" + WALLPACK.acc.join(", ") + ")." };
    const parts = { watts: Number(seg.watt), output: WP_LABELS.effect[effect], cct: WP_LABELS.cct[cct], accessory: WP_LABELS.acc[acc] };
    parts.means = [parts.watts + "W", parts.output, parts.cct, parts.accessory].join(" \u00b7 ");
    return { ok: true, pn, family: "Prime Wallpack", checked: true, codes: Object.assign(seg, { acc }), parts,
      short: "Prime Wallpack " + seg.watt + "W" + (effect === "L" ? " \u00b7 Low output" : "") };
  }
  if (!RE_GENERIC.test(pn)) return { ok: false, pn, error: "An LED Connection part number starts LC- and uses letters, digits and dashes." };
  return { ok: true, pn, family: "", checked: false };
}

/* Walmart A-05 design labels -> part numbers, decided by Dino 2026-10-20
   (pole heads straight square arm, wall heads and S10 yoke, TY5SW -> T5S,
   TY4W -> T4, black, no sensor, S10 CRI 70). They APPLY on any job with
   that design label until LED Connection saves a different number for it
   (Dino, on the pin card: "I need you to upload the codes here"). Each is
   checked against the order logic by tests/parts.test.js. */
const DECIDED = {
  "LC-SLOT-S-S1-NV-40-70-TY4W-W-N": "LC-SLOT-75W-NV-L5-XX-40-70-T4-U-BK",
  "LC-SLOT-S-S1-NV-40-70-TY4W-W": "LC-SLOT-75W-NV-L5-XX-40-70-T4-U-BK",
  "LC-SLOT-145-HV-L5-50-TY03": "LC-SLOT-145W-HV-L5-XX-50-70-T3-U-BK",
  "LC-SLOT-L-L3-HV-50-70-TY5SW": "LC-SLOT-230W-HV-L5-XX-50-70-T5S-SS-BK",
  "LC-SLOT-XL-XL1-HV-50-70-TY5SW": "LC-SLOT-300W-HV-L5-XX-50-70-T5S-SS-BK",
  "LC-SLOT-XL-XL2-HV-30-70-TY5S": "LC-SLOT-420W-HV-L5-XX-30-70-T5S-SS-BK",
  /* Wall packs (Dino, same day): FCW-45 (45W) -> the 40W Prime Wallpack, as
     on Kroger; FCW-20 (20W) -> the 40W low-output tier. 4000K, no accessory. */
  "FCW-45-NV-740-CT": "LC-WP-40W-H-40K",
  "FCW-20-NV-740-CT": "LC-WP-40W-L-40K",

  /* Kroger 345 A-02 (Dino, 2026-10-20), from what NetSuite SO636 shipped:
     the Optimus heads are 230W fixtures (230W in the part number, the
     hardware), bronze, 4000K CRI 80, straight arm, set down to the design's
     watts on site; S01 and S02-HS are the same fixture, S02-HS adds the
     shield. Wall packs, flood and downlight have no order logic here, so
     they carry the LC item number that shipped (not checked). */
  "LC-SLOT-L-L1-480-40-70-TY5SW": "LC-SLOT-230W-HV-L5-XX-40-80-T5S-SS-BR",
  "LC-SLOT-L-S1-480-40-70-TY4W": "LC-SLOT-230W-HV-L5-XX-40-80-T4-SS-BR",
  "LC-SLOT-L-S1-480-40-70-TY4W-HS": "LC-SLOT-230W-HV-L5-XX-40-80-T4-SS-BR",
  "FCW-20-740-277-CT": "LC-FWP-WS-3CCT",
  "FCW-45-740-277-CT": "LC-FWP-WS-3CCT",
  "LC-FL32A-40-480-40": "LC-FL-WS-3CCT-SF",   /* slip fitter, not yoke (Dino, 2026-10-21) */
  "LC-UDL-10-16W-277-40-GR": "LC-UDL-8-A"
};

/* How a head with that design label is set up on site, where the part
   number alone does not say it (a selectable fixture, a shield, a goof
   ring). Shown under the part number on the material line, the pin card
   and the job sheet. Settings come from the design; what ships with it
   from the sales order. */
const SETUP = {
  "LC-SLOT-L-L1-480-40-70-TY5SW": "Lens (Type V square) and 4000K board come inside the fixture; the 240W driver ships in its own box. The design runs each head at 181W.",
  "LC-SLOT-L-S1-480-40-70-TY4W": "Set to 75W with the fixture's dip switch (design 74W).",
  "LC-SLOT-L-S1-480-40-70-TY4W-HS": "Set to 75W with the fixture's dip switch (design 74W). Fit the house-side shield (LC-SLOT-LG-SHIELD, shipped with it) on site.",
  "FCW-20-740-277-CT": "Selectable wall pack: set to 20W and 4000K.",
  "FCW-45-740-277-CT": "Selectable wall pack: set to 45W and 4000K.",
  "LC-FL32A-40-480-40": "Selectable flood on its slip fitter: set to 40W and 4000K. It runs on 120-277V: wire it through the 480V-to-277V step-down transformer in its junction box (shipped with it).",
  "LC-UDL-10-16W-277-40-GR": "Selectable 8\" downlight: set to 16W and 4000K. Fit the goof ring (LC-UDL-8-GR) to cover the old 10\" opening."
};

/* The same in a few words, for the material check row (Dino, 2026-10-27,
   from the Claude Design canvas: "less text first"); the full line stays in
   DOCUMENTS, on the pin card and on the job sheet. One per SETUP entry
   (tests/parts.test.js). */
const SETUP_SHORT = {
  "LC-SLOT-L-L1-480-40-70-TY5SW": "Driver in its own box · runs at 181W",
  "LC-SLOT-L-S1-480-40-70-TY4W": "Dip switch to 75W",
  "LC-SLOT-L-S1-480-40-70-TY4W-HS": "Dip switch to 75W · fit the house-side shield",
  "FCW-20-740-277-CT": "Set to 20W · 4000K",
  "FCW-45-740-277-CT": "Set to 45W · 4000K",
  "LC-FL32A-40-480-40": "Set to 40W · 4000K · through the 480V step-down",
  "LC-UDL-10-16W-277-40-GR": "Set to 16W · 4000K · fit the goof ring"
};

module.exports = { check, DECIDED, SETUP, SETUP_SHORT, OPTIMUS, LABELS, WALLPACK };
