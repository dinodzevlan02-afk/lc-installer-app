/* LC Installer App - LED Connection installation guides (PDF) per product.

   An Optimus head is installed the way its BRACKET mounts, so there is one
   guide per bracket code of the order logic (api/shared/parts.js), and a
   product line gets the guide for the bracket in its saved part number.
   The guides are LED Connection's own, built by tools/guides/build_guides.py
   from the supplier's bracket guides (supplier name and codes never shown)
   into app/guides/optimus/, which is published with the site.

   READY lists the brackets whose PDF is in app/guides/optimus/. The API is
   deployed apart from app/, so it cannot look; tests/guides.test.js fails
   when this list and the folder disagree. A bracket not yet ready still
   names its guide, marked not ready, so the page can say it is coming. */
const BRACKET_NAMES = { F: "Slipfitter", SS: "Straight square arm", SR: "Straight round arm", R: "Adjustable straight arm", U: "Yoke", T: "Trunnion" };
const READY = ["F", "R", "SR", "SS", "T", "U"];

const file = code => "LC-Optimus-Installation-Guide-" + code + ".pdf";

/* Products with no order logic (Kroger 345, Dino 2026-10-21): one guide per
   LC part number, built by the same tools/guides/build_guides.py from the
   product's own instructions (tools/guides/content/FL-Y, FL-SF, FWP).
   PART_READY lists the files committed under app/guides/ (paths below it);
   tests/guides.test.js keeps it in step with the flood/ and wallpack/ folders. */
const BY_PART = {
  "LC-FL-WS-3CCT-Y": { family: "Floodlight", bracket: "Y", bracketName: "Yoke", file: "flood/LC-Floodlight-Installation-Guide-Y.pdf" },
  "LC-FL-WS-3CCT-SF": { family: "Floodlight", bracket: "SF", bracketName: "Slip fitter", file: "flood/LC-Floodlight-Installation-Guide-SF.pdf" },
  "LC-FWP-WS-3CCT": { family: "NightShade wall pack", bracket: "FWP", bracketName: "Wall mount", file: "wallpack/LC-NightShade-Installation-Guide-FWP.pdf" }
};
const PART_READY = [
  "flood/LC-Floodlight-Installation-Guide-Y.pdf",
  "flood/LC-Floodlight-Installation-Guide-SF.pdf",
  "wallpack/LC-NightShade-Installation-Guide-FWP.pdf"
];

function byPart(pn) {
  const g = BY_PART[String(pn || "").trim().toUpperCase()];
  if (!g) return null;
  return {
    family: g.family, bracket: g.bracket, bracketName: g.bracketName,
    title: g.family + " installation guide · " + g.bracketName,
    url: "/guides/" + g.file,
    ready: PART_READY.includes(g.file)
  };
}

/* -> { family, bracket, bracketName, title, url, ready } or null */
function forPart(check) {
  if (check && check.ok && check.family !== "Optimus") return byPart(check.pn);
  if (!check || !check.ok || check.family !== "Optimus" || !check.codes) return null;
  const code = check.codes.bracket;
  if (!BRACKET_NAMES[code]) return null;
  return {
    family: "Optimus", bracket: code, bracketName: BRACKET_NAMES[code],
    title: "Optimus installation guide · " + BRACKET_NAMES[code] + " bracket",
    url: "/guides/optimus/" + file(code),
    ready: READY.includes(code)
  };
}

module.exports = { forPart, READY, BRACKET_NAMES, file, BY_PART, PART_READY };
