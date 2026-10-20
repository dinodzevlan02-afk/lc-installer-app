# Sites kept in the installer app

For a project that lives in the installer app only, not in the customer
portal (Kroger 345 first, Dino 2026-10-20). One folder per project:

| File | What | From |
|---|---|---|
| `fixtures.csv` | the LED Audit app's project export, one row per head (photo links removed: signed, they expire) | job folder in SharePoint, or the audit app's export |
| `survey-mapping.tsv` | the Field Survey's Audit Results sheet: audit pin -> design tag, excluded | `audit_results.xlsx`, sheet Audit Results, saved as tab-separated |
| `project.json` | name, address, customer, the approved design's luminaire schedule per tag (label, heads, watts, MH, tilt), reasons for excluded and removed heads, and `added`: heads the design has where the audit has none (placed opposite a named head across its pole, with the line the installer reads) | written by hand from the design PDF |

    node tools/sites/build-site.js KR-00345-NV     -> tools/sites/out/KR-00345-NV.site.json

The build stops on any audit row it cannot place and prints heads per tag
against the design. Upload the file on the home page (Projects > + Add
another project > Upload site file), then start the job and tick the
installers. Uploading again replaces the site and keeps every saved pin.

The design is the source for every product field; the survey mapping only
says which tag a pin takes. `tests/sites.test.js` rebuilds KR-00345-NV and
checks it against the A-02 schedule.
