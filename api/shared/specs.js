/* LC Installer App - LED Connection's own spec sheets for products the
   catalog cannot give us (no catalog id, no unique family name), bundled in
   app/specs/ like the installation guides, picked by the part number.

   The PDFs are LED Connection's own published spec sheets (SharePoint
   LEDDocuments > LED > Sales > Marketing > Marketing-2025 > LED >
   SpecSheets), public like every catalog spec sheet. READY lists the files
   committed in app/specs/ (the API cannot see app/ on Azure);
   tests/specs.test.js fails when READY and the folder disagree. */
const BY_PART = {
  "LC-FWP-WS-3CCT": "LC-Nightshade-Full-Cutoff-Wallpack.pdf",
  "LC-UDL-8-A": "LC-Universal-Downlight-Series.pdf"
};
const READY = [];

/* -> "/specs/{file}" for a part number whose spec sheet is bundled, else null */
function forPart(pn) {
  const f = BY_PART[String(pn || "").trim().toUpperCase()];
  return f && READY.includes(f) ? "/specs/" + f : null;
}

module.exports = { forPart, BY_PART, READY };
