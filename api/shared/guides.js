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

/* -> { family, bracket, bracketName, title, url, ready } or null */
function forPart(check) {
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

module.exports = { forPart, READY, BRACKET_NAMES, file };
