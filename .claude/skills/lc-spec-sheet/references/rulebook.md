# Skill brief — SPEC SHEET

**Kind: `output`.** Lighting and Screens are *sourcing* skills: they find and negotiate.
This one is different. It runs **after** sourcing closes and turns a settled supplier quote
into an LED Connection spec sheet — the document that goes to customers, contractors,
estimators and inspectors.

That difference is the whole brief. Everything a sourcing skill does is internal and
reversible. **A spec sheet is published.** A wrong number on it is quoted back at you by a
plan reviewer eighteen months later.

---

## 1. THE THREE RULES THAT MATTER MORE THAN THE LAYOUT

### 1.1 Never name the factory. Not anywhere. Not once.

Read the two reference sheets — `Omnitron_Highbay_SpecSheet_LC-LHB-OH` and
`Triproof_Vaporlight_SpecSheet_LC-TP`. Twelve pages and four pages respectively, and the
supplier is **not mentioned a single time**. The product is *Omnitron Series*, the SKU is
*LC-LHB-OLH*, the contact is *bids@ledconnection.com*.

This is not modesty, it is the business. LC is the supplier of record on the job. A spec
sheet that names the factory hands the customer a way to buy around us and hands a
competitor our vendor. There is no version of this document where the factory appears.

**This extends to fingerprints, not just names.** Do not carry across the supplier's model
number, their part-number scheme, their marketing phrases, their photography with their
badge in the corner, or their datasheet's distinctive table layout. Rewrite the copy.

### 1.2 Only publish a certification we have actually verified

A DLC Product ID or a UL file number on this sheet is a claim **LC** is making to a utility
and to an inspector, under LC's name. The supplier's word is not verification.

| Field | Publish only if |
|---|---|
| DLC Product ID | The ID is recorded AND `dlc_verified: true`. The QPL is behind a sign-in wall, so this means a human checked it. **`dlc_verified: false` never reaches the sheet.** |
| UL / ETL file number | We have the number and the standard, not just the word "certified" |
| FCC ID (screens) | Verified in the public FCC database — this one is genuinely checkable |
| L70 / lumen maintenance | Backed by an LM-80 report we hold, projected per TM-21 |
| Efficacy, lumens, CRI | From a test report, not a catalogue headline |

**If a field is not verified, it is omitted — not estimated, not rounded, not carried over
from the supplier's brochure.** An incomplete spec sheet is a normal thing. A confident
wrong one is a liability.

### 1.3 Nothing commercial

No cost, no landed cost, no margin, no supplier pricing, no MOQ, no incoterm, nothing from
the `.priv` columns of the Master Project Tool. This sheet describes a product. Price lives
in a quote, and the quote is a different document with a different audience.

---

## 2. THE ANATOMY, FROM THE REFERENCE SHEETS

Both examples follow the same skeleton. Match it.

**Page 1 — cover.** Family name (OMNITRON SERIES). Product type (LINEAR HIGH BAY
SELECTABLE). Headline efficacy (`≤170 LM/W`). A short capability tagline in caps
(*SELECTABLE POWER. CLEAN INSTALLATION.*). Six chips: **WATTAGE · VOLTAGE · L70 or LIFESPAN ·
WARRANTY · CRI · CCT**. Two or three sentences of positioning. *"For custom solutions please
contact our sales representative."* Footer on every page: phone, web, **bids@ledconnection.com**,
915 E Dale Ave Ste 110, Henderson NV 89044.

**Page 2 — description.** A PRODUCT DESCRIPTION paragraph. An OVERVIEW list of eight to
twelve technical bullets. DIMENSIONS or OPTIONS. A badge row (*wattage selectable*, *1-10V
dimming*, *5 years*, *50000h lifespan*, *color selectable*). The LC SKU shown prominently.

**Page 3 — electrical data and ORDER LOGIC.** The electrical table. The lumen-maintenance
note, worded as the references do: *"Calculated L70 @25°C ambient: 186,000 hours. Lumen
maintenance data is based on LED testing per IES LM-80 and projected per IES TM-21."* Then
the SKU builder — numbered segments, one option per segment, with a sample code:

```
LC - TP65X2 - 20 - X
     [02][03]  [04]  [05]
```

**Page 4+ — photometrics.** A candela polar plot per lumen package, labelled with the
wattage, CCT and efficacy it represents.

---

## 3. THE PHOTOMETRIC PAGE IS WHY IES FILES ARE A SOURCING GATE

You cannot draw that polar plot without a real IES file. This is the moment the lighting
skill's hard gate — *"IES photometric files for every SKU and distribution"* — stops being
paperwork and becomes the thing standing between us and a finished document.

**If the IES file is missing, omit the photometric page and say so in the run summary.**
Never trace a curve from the supplier's PDF and never reuse a sibling SKU's distribution.
A photometric plot is what a designer runs a layout against; a wrong one produces a failed
site that gets rebuilt at our cost.

---

## 4. SKU AND FAMILY NAMING

The family name is **ours** and it is a business decision, not a generated string. Optimus,
Roswell Series, Prime Wallpack, Sentinel Gen 2, Gridlight, Omnitron, CBT, Titanus, Triproof,
Windcharger, Magnus Round, Colossus, Bumblebee.

**Every code starts with LC.** Dino's rule, 2026-09-10, and it is structural rather than
cosmetic: in both reference sheets the SKU builder's numbered segments start at **02**,
because **segment 01 is `[BRAND]` and `[BRAND]` is always `LC`**. `LC - TP65X2 - 20 - X`.
So the prefix is not a label bolted onto the front of a code, it is the first segment of the
code. `rebrand.py` normalises any SKU that arrives without it, because a prefix typed
inconsistently breaks the join into the Master Project Tool, where Type ID is the key.

**Never invent a family name or an LC SKU prefix.** Both are catalogue decisions with
downstream effects in the Master Project Tool, the estimating sheets and the quote pipeline,
where **Type ID is the join key**. Ask Dino. If he has not assigned one, the sheet is drafted
with the prefix marked and does not ship.

Order-logic segments must describe options that **actually exist** in what we agreed to buy.
If the quote covers 4000K and 5000K, the CCT segment has two options — not the four the
factory's catalogue lists.

---

## 5. WHEN THIS SKILL RUNS

**Trigger, Dino's rule 2026-09-11 — build as soon as all THREE are true:**

1. **A confirmed UL/ETL listing** — a file number AND the named standard.
2. **A vendor spec sheet** in the project folder.
3. **Pricing** in the project folder.

That replaces the old `closed`-with-selected-supplier trigger, which produced the sheet long
after it was useful. The sheet now appears while the negotiation is live, carrying its
PRE-RELEASE band and placeholder family name until Dino settles those.

### The UL gate — both domains, no exceptions

**No confirmed UL/ETL listing means no LC spec sheet gets built at all.** Not a warning, a
block, enforced in `build.check()` and again before the build in `project-sheet.py`.

The reasoning is already company policy: `company-profile.md` hard requirement 2 is a
verifiable UL or ETL file number, and a supplier failing it *"cannot be used on our work"*.
Publishing an LC-branded sheet for a product we cannot legally install is the same class of
error as publishing an unverified certification — a document that looks finished and is wrong.

**What does not count as confirmation:**

- The word "certified", or a UL mark printed on a brochure.
- A file number with no standard named. `UL 1598` for a luminaire, `UL 48` for a sign or
  display — make them name it.
- **A listing on a component inside the assembly.** A UL-listed power supply in a screen with
  no listing of its own is not a listed screen. That is the live case: the first display sheet
  was withdrawn 2026-09-11 on exactly that distinction.

Before starting, confirm all of:

- [ ] A supplier is selected and the request is closed — not `comparing`
- [ ] Certifications verified per §1.2, with the DLC ID checked by a human
- [ ] IES files received, or their absence noted for §3
- [ ] Dino has assigned the family name and LC SKU prefix
- [ ] The option set for each order-logic segment is confirmed, not copied

**Missing any of these is a normal outcome.** Report what is missing and stop. A spec sheet
that ships with a placeholder in it is worse than no spec sheet, because it looks finished.

---

## 5a. DISPLAYS — THE SAME TEMPLATE, A DIFFERENT SHEET

Settled 2026-09-11. **Screens rebrand onto the same LC-TP template as lighting** — Dino's
call. One catalogue, one look. What changes is the data, not the design.

Until this section existed the skill was lighting all the way down and screens appeared in it
exactly once, as a row for FCC ID. Everything else — the cover chips, the electrical table,
§3's photometric gate — assumed a luminaire. A screen run through that would have produced a
sheet with a CRI column and an empty LUMEN MAINTENANCE panel, which is the failure §5 warns
about: it looks finished.

### The six cover chips

**PITCH · BRIGHTNESS · TRANSPARENCY · REFRESH · IP · WARRANTY.** Fixed, per Dino.
`cover.chips` takes any six label/value pairs, so this needs no code — but it is not a free
choice either. These six are the sheet.

### What a display makes meaningless

MASTER.md asks this question of every new category, and it was never asked of the *output*
skill. The answer for screens is the same list `skills.json` already carries for sourcing:

**Never on a display sheet:** a DLC line of any kind, IES files, a photometric page, LM-79 /
LM-80 / TM-21, efficacy, CRI, CCT, lumen maintenance. A display emits content, not a
distribution. The display example in `schema.json` has **no `dlc_product_id` and no
`dlc_verified` key at all** — not set to null, absent — because a null field is an invitation
to fill it in.

§3 of this brief is lighting-only. There is no page 4 on a screen sheet.

### What replaces them

| Block | Display content |
|---|---|
| `cover.headline` | Brightness or transparency — the one number that sells it. On lighting this is efficacy |
| `electrical.title` | **TECHNICAL DATA**, not ELECTRICAL DATA |
| `electrical.columns` | Model · Pitch (H × V) · Brightness · Transparency · Refresh · Power avg/max |
| `certifications` | `ul_standard` **named** (UL 48 is the likely one), `ul_file_number`, `fcc_id`, `control_system` |
| closing callout | Omitted. `callout_body` empty means the panel is not drawn at all |

**`control_system` is published deliberately.** Novastar / Colorlight / proprietary is a
lock-in decision the customer inherits, and it is a technical fact rather than a commercial
one, so §1.3 does not exclude it. Spare-module ratio is the opposite — that belongs in the
quote, not here.

**`fcc_id` is the one certification on a screen sheet that is genuinely verifiable** in a
public database. Insist on it. `ul_standard` must be named, never "UL certified" — a supplier
who cannot name the standard has not been through it.

### Two things that will bite on the first real one

- **Asymmetric pitch.** Transparent product is commonly 3.91 mm H × 7.81 mm V. Publishing a
  single "P3.9" is wrong and a plan reviewer will catch it. Both numbers, always.
- **Brightness is quoted at peak.** If a supplier states a derate, the derated working figure
  is the one that ships on the sheet. The `electrical.note` in the display example says so.

### Naming

No display family name or LC SKU prefix exists yet. §4 applies unchanged: **both are Dino's
to assign and are never generated.** The display example carries `<<ASSIGNED BY DINO>>` markers
and **must not ship with them in place** — that is a §5 stop, not a warning.

---

## 6. OUTPUT

`<Family>_<Type>_SpecSheet_<LC-SKU>.pdf`, Letter, into `Sourcing Dino/Spec Sheet Drafts/`
on the Engineering library (falls back to the personal OneDrive, then local).

**The renderer is `overlay.py`, and it uses the LC-TP PDF itself as the canvas.** This is
the method that produced the sheets Dino accepted in his Sep-9 chat, and it replaces two
HTML/CSS attempts he rejected. `assets/template_LC-TP.pdf` is imported page by page as a
vector XObject; the Triproof-specific text, photos and drawings are **redacted out of the
content stream** (not painted over — they must not survive in search or copy); our content
is set into the same rectangles. Nothing is approximated because nothing is redrawn that
did not have to be. The only things redrawn are genuinely variable in shape: the
order-logic segment columns (their count is ours), the electrical table, and everything on
page 3 below the sample-code panel, which is laid out in flow because the template fixes
those boxes at heights sized for four tall option columns.

`build.py` + `theme.py` (HTML → headless Chrome) remain as a fallback if the template PDF
is missing, and as the source of the `check()` guards `overlay.py` still runs first.

**The design lives in `theme.py`, and it was read off the reference sheets by LOOKING at
them, not by extracting their text.** The first build did the opposite — it rebuilt the
*content* of the Omnitron and Triproof sheets and ignored their *design* — and Dino's
verdict was immediate: *"this template is not good."* He was right. A spec sheet that does
not look like the rest of the catalogue reads as a document from some other company, and no
amount of correct data fixes that. What the references actually do:

- Navy left rail on the cover carrying the family name rotated in orange, logo at its foot
- Hero product photo over an orange circuit-trace motif
- Product type in small grey caps **above** a very large black family name, short orange rule
- Six spec columns divided by thin rules — orange caps labels over large bold values
- Section headers as filled navy bars, white caps, thin orange rule running to the right edge
- Cream callouts with a thick orange left bar
- Order-logic sample code on a navy panel, brand and series in orange, segments marked below
- Navy footer bar on every page with orange field labels

**The real LED Connection wordmark is in `assets/`**, cropped from the reference PDF at
400 dpi — it is vector artwork there, not an embedded image, so it cannot be extracted; it
has to be rendered and clipped. The hand-drawn SVG placeholder it replaced looked nothing
like it and, unconstrained, rendered at a quarter of the page on inner sheets.

**Vendor product photos may be used as the hero** when they carry no vendor badge or
watermark — the fixture is the product LC sells. The photograph is not the fingerprint;
the logo in its corner would be.

Every published number carries a provenance note in the build record saying which document
it came from.

**Two build hazards, both silent:** headless Chrome sharing the user's running profile
exits 0 without writing (use `--user-data-dir`); and writing a PDF straight into a syncing
OneDrive folder fails with WinError 32 while Chrome still reports success. `to_pdf()`
renders to temp, verifies size, then copies with retry and a versioned fallback name.
