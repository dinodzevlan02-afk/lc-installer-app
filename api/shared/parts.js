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
   A part number that looks like an Optimus one must be a valid one: the
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
    return { ok: true, pn, family: "Optimus", checked: true, short: "Optimus " + seg.watt + "W \u00b7 " + dist, parts: {
      watts: Number(seg.watt), volt: LABELS.volt[volt], sensor: LABELS.sensor[sensor], cct: LABELS.cct[cct], cri: LABELS.cri[cri],
      optic: LABELS.dist[dist], bracket: LABELS.bracket[bracket], color: LABELS.color[color] } };
  }
  if (!RE_GENERIC.test(pn)) return { ok: false, pn, error: "An LED Connection part number starts LC- and uses letters, digits and dashes." };
  return { ok: true, pn, family: "", checked: false };
}

/* Walmart A-05 design labels -> part numbers, decided by Dino 2026-10-20
   (pole heads straight square arm, wall heads and S10 yoke, TY5SW -> T5S,
   TY4W -> T4, black, no sensor, S10 CRI 70). Offered to LED Connection as
   SUGGESTIONS on a job that has no part number saved for that label; they
   apply only once saved. Never shown to installers. */
const SUGGESTED = {
  "LC-SLOT-S-S1-NV-40-70-TY4W-W-N": "LC-SLOT-75W-NV-L5-XX-40-70-T4-U-BK",
  "LC-SLOT-S-S1-NV-40-70-TY4W-W": "LC-SLOT-75W-NV-L5-XX-40-70-T4-U-BK",
  "LC-SLOT-145-HV-L5-50-TY03": "LC-SLOT-145W-HV-L5-XX-50-70-T3-U-BK",
  "LC-SLOT-L-L3-HV-50-70-TY5SW": "LC-SLOT-230W-HV-L5-XX-50-70-T5S-SS-BK",
  "LC-SLOT-XL-XL1-HV-50-70-TY5SW": "LC-SLOT-300W-HV-L5-XX-50-70-T5S-SS-BK",
  "LC-SLOT-XL-XL2-HV-30-70-TY5S": "LC-SLOT-420W-HV-L5-XX-30-70-T5S-SS-BK"
};

module.exports = { check, SUGGESTED, OPTIMUS, LABELS };
