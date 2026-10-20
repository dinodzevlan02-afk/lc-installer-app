/* Build a site file for the installer app (format "lc-site", the shape the
   customer portal stores) from three things LED Connection already has:

     tools/sites/{id}/fixtures.csv        the LED Audit app's project export, one row per head
     tools/sites/{id}/survey-mapping.tsv  the Field Survey's Audit Results sheet: which
                                          audit pin takes which design tag, which are excluded
     tools/sites/{id}/project.json        name, address, the approved design's luminaire
                                          schedule (tag -> label, qty, watts, MH, tilt) and
                                          the reasons for excluded / removed heads

     node tools/sites/build-site.js KR-00345-NV      -> tools/sites/out/KR-00345-NV.site.json

   Then upload the file on the installer app's home page (Projects > Upload
   site file). Nothing is written to the customer portal.

   The DESIGN is the source for every product field; the mapping only says
   which tag a pin takes. The build stops on anything it cannot place: an
   audit row with no mapping and no stated reason, a mapping row with no
   audit row, or a tag the design does not have. It prints the heads per tag
   against the design's quantities, so a missing pin shows before upload. */
const fs = require("fs");
const path = require("path");

function parseCsv(text, sep) {
  text = text.replace(/^﻿/, "");
  const rows = [];
  let row = [], cell = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') q = false;
      else cell += c;
    } else if (c === '"') q = true;
    else if (c === sep) { row.push(cell); cell = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(cell); cell = "";
      if (row.length > 1 || row[0] !== "") rows.push(row);
      row = [];
    } else cell += c;
  }
  if (cell !== "" || row.length) { row.push(cell); rows.push(row); }
  const head = rows.shift().map(h => h.trim());
  return rows.map(r => Object.fromEntries(head.map((h, i) => [h, r[i] == null ? "" : r[i]])));
}

/* Metres between two lat/lng points (small distances). */
function metres(a, b) {
  const k = Math.PI / 180, R = 6371000;
  const x = (b.lng - a.lng) * k * Math.cos((a.lat + b.lat) / 2 * k), y = (b.lat - a.lat) * k;
  return Math.sqrt(x * x + y * y) * R;
}

function build(dir) {
  const project = JSON.parse(fs.readFileSync(path.join(dir, "project.json"), "utf8"));
  const audit = parseCsv(fs.readFileSync(path.join(dir, "fixtures.csv"), "utf8"), ",");
  const mapping = parseCsv(fs.readFileSync(path.join(dir, "survey-mapping.tsv"), "utf8"), "\t");
  const tags = project.design.tags;
  const errors = [], notes = [];
  const mapById = {};
  mapping.forEach(m => { mapById[String(m.ID).trim()] = m; });
  const auditIds = new Set(audit.map(r => String(r.id).trim()));
  mapping.forEach(m => { if (!auditIds.has(String(m.ID).trim())) errors.push("Mapping row " + m.ID + " has no audit row."); });

  const data = [], solutions = {}, excluded = {};
  const pos = r => ({ lat: parseFloat(r.latitude), lng: parseFloat(r.longitude) });
  audit.forEach((src, idx) => {
    const r = Object.assign({}, src);
    delete r.images;                       /* signed photo links: they expire, and are credentials */
    const id = String(r.id).trim(), m = mapById[id];
    const group = m && String(m.Group || "").trim();
    if (!String(r["pole id"] || "").trim() && group) { r["pole id"] = group; r["pole id source"] = "Field Survey group"; }
    if (m && /^yes$/i.test(String(m.Excluded).trim())) {
      excluded[idx] = true;
      r.deactivated = (project.excluded || {})[r.schedule] || "Not in the design";
    } else if (m) {
      const tag = String(m["Sol. Tag"]).trim(), d = tags[tag];
      if (!d) { errors.push("Audit row " + id + " maps to " + tag + ", which the design does not have."); }
      else {
        const surveyLabel = String(m["Sol. Label"]).replace(/\(\d+\)$/, "").trim();
        if (surveyLabel && surveyLabel !== d.label) notes.push(tag + ": the survey labelled it " + surveyLabel + ", the design says " + d.label + " (design used).");
        const auditMh = parseFloat(r["mounting height"]);
        const mh = Array.isArray(d.mh) ? (d.mh.includes(auditMh) ? auditMh : d.mh[0]) : d.mh;
        solutions[idx] = {
          fam: d.fam, lc_sku: d.label, cat: d.cat, cct: d.cct, volt: d.volt, watt: d.watt,
          tag, arrangement: d.arrangement, mh, tilt: d.tilt,
          specific: d.specific || undefined, prodId: d.prodId || undefined, specSheetUrl: d.specSheetUrl || undefined
        };
      }
    } else if ((project.removed || {})[id]) {
      excluded[idx] = true;
      r.deactivated = project.removed[id];
    } else errors.push("Audit row " + id + " (" + r.schedule + ") is not in the mapping and has no stated reason.");
    data.push(r);
  });

  /* A removed head with no pole id joins the pole of the nearest mapped head
     within 10 m (the other head of the double it was part of). */
  data.forEach((r, i) => {
    if (!excluded[i] || String(r["pole id"] || "").trim() || !(project.removed || {})[String(r.id).trim()]) return;
    let best = null;
    data.forEach((o, j) => {
      if (j === i || !solutions[j] || !String(o["pole id"] || "").trim()) return;
      const d = metres(pos(r), pos(o));
      if (d <= 10 && (!best || d < best.d)) best = { d, pole: o["pole id"] };
    });
    if (best) { r["pole id"] = best.pole; r["pole id source"] = "nearest head, " + best.d.toFixed(1) + " m"; }
  });

  const counts = {};
  Object.keys(solutions).forEach(i => { if (!excluded[i]) counts[solutions[i].tag] = (counts[solutions[i].tag] || 0) + 1; });
  const checks = Object.keys(tags).map(t => ({ tag: t, design: tags[t].qty, pins: counts[t] || 0 }));
  checks.forEach(c => { if (c.pins !== c.design) notes.push(c.tag + ": the design has " + c.design + " heads, the audit gives " + c.pins + " pins."); });

  const file = {
    format: "lc-site", version: 1,
    project: { id: project.id, name: project.name, address: project.address, customer: project.customer, kind: project.kind, installDate: project.installDate || "" },
    source: Object.assign({}, project.source, { built: new Date().toISOString().slice(0, 10), builder: "tools/sites/build-site.js" }),
    site: { datasets: [{ id: project.dataset.id, label: project.dataset.label, data, solutions: JSON.parse(JSON.stringify(solutions)), excluded }] }
  };
  return { file, errors, notes, checks, rows: data.length, heads: Object.values(counts).reduce((a, b) => a + b, 0), excluded: Object.keys(excluded).length };
}

module.exports = { build, parseCsv };

if (require.main === module) {
  const id = process.argv[2];
  if (!id) { console.error("usage: node tools/sites/build-site.js <project id>"); process.exit(2); }
  const out = build(path.join(__dirname, id));
  console.log(id + ": " + out.rows + " audit rows, " + out.heads + " heads to install, " + out.excluded + " excluded");
  console.log("tag        design  pins");
  out.checks.forEach(c => console.log(c.tag.padEnd(10) + String(c.design).padStart(6) + String(c.pins).padStart(6) + (c.pins !== c.design ? "   <-" : "")));
  [...new Set(out.notes)].forEach(n => console.log("note: " + n));
  if (out.errors.length) { out.errors.forEach(e => console.error("ERROR: " + e)); process.exit(1); }
  fs.mkdirSync(path.join(__dirname, "out"), { recursive: true });
  const f = path.join(__dirname, "out", id + ".site.json");
  fs.writeFileSync(f, JSON.stringify(out.file));
  console.log("wrote " + path.relative(process.cwd(), f) + " (" + Math.round(fs.statSync(f).size / 1024) + " KB)");
}
