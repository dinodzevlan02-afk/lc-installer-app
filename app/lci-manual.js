/* LC Installer App - install guide for one product on one job.

   Built from what the app knows for certain: the design's own figures for
   this job (mount height, arrangement, tilt, arm, options, tags, how many)
   and the LC catalog (photo, mounting options, voltage range, the
   manufacturer's PDFs). The steps are general good practice, written so
   that anything product-specific (wire colours, torque, drilling, sealing)
   points to the fixture's own label and instructions instead of guessing.
   Marked DRAFT until LED Connection approves the wording (2026-10-20). */
(function () {
  'use strict';
  var esc = LCI.esc, q = new URLSearchParams(location.search);
  var JOB = q.get('job') || '', KEY = q.get('p') || '';
  document.getElementById('back').href = './job.html?id=' + encodeURIComponent(JOB) + '#install';

  function kindOf(b) {
    var c = ((b.catalog && b.catalog.cat) || b.cat || b.fam || '').toLowerCase();
    if (/wall/.test(c)) return 'wall';
    if (/flood/.test(c)) return 'flood';
    if (/area|site|pole|shoebox/.test(c)) return 'area';
    return 'other';
  }

  /* The product's input range against what the audit recorded at the
     fixtures it replaces. Only says "check" - never decides. */
  function voltageNote(b, pins) {
    var site = {};
    pins.forEach(function (p) { if (p.existing.voltage) site[p.existing.voltage] = 1; });
    var sv = Object.keys(site), pv = b.volt || ((b.catalog && b.catalog.volts) || []).join(' / ');
    if (!pv && !sv.length) return '';
    return '<li><b>Voltage.</b> This product: <b>' + esc(pv || 'see label') + '</b>. ' +
      (sv.length ? 'The audit recorded <b>' + esc(sv.join(', ')) + '</b> at the fixtures it replaces. ' : 'The audit did not record the site voltage. ') +
      'Measure the circuit before connecting. If it is outside the range on the fixture label, stop and call LED Connection.</li>';
  }

  function mountSteps(kind, b, sol) {
    var s = [];
    var mh = sol.mh ? ' at <b>' + esc(sol.mh) + ' ft</b> mounting height' : '';
    if (kind === 'area') {
      s.push('Fit the mount the design calls for' + (sol.specific ? ' (<b>' + esc(sol.specific) + '</b>)' : '') + mh + '. Use the arm, slip fitter or adapter supplied for this pole; check it fits the pole top or drilling before lifting.');
      if (sol.arrangement) s.push('Arrangement on the pole: <b>' + esc(sol.arrangement) + '</b>. Pins on the same pole in the app are the heads of that pole.');
      s.push('Turn the head so its optic throws light where the design shows. The optic (' + esc(beamOf(b.sku) || 'see SKU') + ') is asymmetric unless it is a Type 5: the street side faces the area being lit, not the pole.');
      if (sol.tilt) s.push('Tilt: <b>' + esc(sol.tilt) + '&deg;</b> as designed.'); else s.push('Mount level (no tilt) unless the design says otherwise.');
      if (sol.armLength) s.push('Arm length: <b>' + esc(sol.armLength) + '</b>.');
    } else if (kind === 'wall') {
      s.push('Mount over the existing wall box or to the wall surface as the fixture instructions describe' + mh + '. Use anchors rated for the wall.');
      s.push('Seal the back plate and any conduit entry against water as the instructions show, keeping the drain or weep holes open.');
      s.push('Light faces down; check the fixture is level and the lens is clear of obstructions.');
    } else if (kind === 'flood') {
      s.push('Fit the mount the design calls for' + (sol.specific ? ' (<b>' + esc(sol.specific) + '</b>)' : '') + mh + '. Tighten the trunnion or knuckle fully once aimed.');
      s.push('Aim' + (sol.tilt ? ' at <b>' + esc(sol.tilt) + '&deg;</b> tilt' : '') + ' toward the area shown in the design. Floods aimed above the horizontal cause glare and light trespass; check with LED Connection before aiming up.');
    } else {
      s.push('Mount as the fixture instructions describe' + mh + '.');
    }
    s.push('Tighten every fastener to the torque in the manufacturer\'s instructions. Use a safety cable where one is supplied.');
    return s;
  }

  function beamOf(sku) {
    var m = String(sku || '').toUpperCase().split('-').filter(function (x) { return /^(T[1-5][SMW]{0,2}|TY\d{1,2}[SMW]{0,2}|TYPE[1-5])$/.test(x); })[0];
    return m || '';
  }

  function render(d) {
    var b = d.site.bom.filter(function (x) { return x.key === KEY; })[0];
    if (!b) { document.getElementById('out').innerHTML = '<p class="msg err">This product is not on this job.</p>'; return; }
    var pins = d.site.pins.filter(function (p) { return p.productKey === KEY && !p.off; });
    var sol = (pins[0] && pins[0].product) || {}, kind = kindOf(b), cat = b.catalog || {};
    var existing = {};
    pins.forEach(function (p) { var k = [p.existing.type, p.existing.tech, p.existing.watts ? p.existing.watts + ' W' : ''].filter(Boolean).join(' · '); if (k) existing[k] = (existing[k] || 0) + 1; });
    var mh = Object.keys(existing).some(function (k) { return /metal halide|mh|hps|sodium|mercury/i.test(k); });
    var byTag = {};
    pins.forEach(function (p) { (byTag[p.tag] = byTag[p.tag] || []).push(p); });
    document.title = b.name + ' - job sheet';

    /* The LED Connection installation guide for this product's bracket,
       from its part number (api/shared/guides.js). */
    var g = b.partNo && b.partNo.guide, guide;
    if (g && g.ready) guide = '<a class="guide-pdf" target="_blank" rel="noopener" href="' + esc(g.url) + '"><span class="k">Installation guide · PDF</span><b>' + esc(g.title) + '</b><span class="muted">Opens the step-by-step guide for this bracket.</span></a>';
    /* Until the bracket guide is ready, the card opens the product's spec
       sheet from the LC catalog (Dino, 2026-10-20: "link the spec sheet in
       it"), so the installer has the product's own document now. */
    else if (b.specSheetUrl) guide = '<a class="guide-pdf" target="_blank" rel="noopener" href="' + esc(b.specSheetUrl) + '"><span class="k">Installation guide · Spec sheet</span><b>' + esc(b.name) + ' spec sheet</b><span class="muted">Opens this product\'s spec sheet from the LC catalog.' + (g ? ' The step-by-step ' + esc(g.bracketName.toLowerCase()) + ' bracket guide is being prepared by LED Connection.' : '') + ' The instructions packed with the fixture come first.</span></a>';
    else if (g) guide = '<div class="guide-pdf off"><span class="k">Installation guide · PDF</span><b>' + esc(g.title) + '</b><span class="muted">Being prepared by LED Connection. Until then, follow the instructions packed with the fixture.</span></div>';
    else guide = '<div class="guide-pdf off"><span class="k">Installation guide · PDF</span><b>' + (b.partNo ? 'No LED Connection guide for this product yet' : 'Shown once LED Connection sets this product\'s part number') + '</b><span class="muted">Follow the instructions packed with the fixture.</span></div>';

    var docs = (b.specSheetUrl ? '<a class="btn" target="_blank" rel="noopener" href="' + esc(b.specSheetUrl) + '">Spec sheet</a>' : '') +
      (cat.docs || []).map(function (x) { return '<a class="btn" target="_blank" rel="noopener" href="' + esc(x.url) + '">' + esc(x.label) + '</a>'; }).join('');

    var h = '<div class="hdr">' + (cat.imageUrl ? '<img class="prod" src="' + esc(cat.imageUrl) + '" alt="" onerror="this.remove()">' : '') +
      '<div><h1>' + esc(b.name) + '</h1>' + (b.partNo ? '<div class="mono">Part no. <b>' + esc(b.partNo.pn) + '</b></div>' : '') +
        (b.partNo ? '' : '<div class="mono muted">Design label ' + esc(b.sku) + '</div>') + '<div class="muted">' + esc(d.job.name) + '</div></div></div>' +
      guide +
      '<div class="draft"><b>LC DRAFT job sheet.</b> Generated from this job\'s design and the LC catalog. The instructions packed with the fixture come first: where they differ, follow them and tell LED Connection.</div>' +
      '<h2>On this job</h2><dl class="kv"><dt>Quantity</dt><dd><b>' + pins.length + '</b> heads</dd>' +
      '<dt>Tags</dt><dd>' + Object.keys(byTag).map(function (t) { return '<b>' + esc(t) + '</b> &times; ' + byTag[t].length; }).join(', ') + '</dd>' +
      (sol.mh ? '<dt>Mount height</dt><dd>' + esc(sol.mh) + ' ft</dd>' : '') +
      (sol.arrangement ? '<dt>Arrangement</dt><dd>' + esc(sol.arrangement) + '</dd>' : '') +
      (b.partNo && b.partNo.parts && b.partNo.parts.means ? '<dt>Part no. means</dt><dd>' + esc(b.partNo.parts.means) + '</dd>'
        : sol.specific && sol.specific !== b.sku ? '<dt>Options</dt><dd>' + esc(sol.specific) + '</dd>' : '') +
      (b.cct ? '<dt>CCT</dt><dd>' + esc(b.cct) + '</dd>' : '') +
      (b.volt ? '<dt>Input</dt><dd>' + esc(b.volt) + '</dd>' : '') +
      (cat.mounts && cat.mounts.length ? '<dt>Mounts made</dt><dd>' + esc(cat.mounts.join(', ')) + '</dd>' : '') +
      '<dt>Replaces</dt><dd>' + (Object.keys(existing).map(function (k) { return esc(k) + ' &times; ' + existing[k]; }).join('<br>') || '-') + '</dd></dl>' +
      (docs ? '<h2>Manufacturer documents</h2><div class="docs">' + docs + '</div>' : '') +

      '<h2>1 · Before you lift</h2><ol>' +
        '<li>Check the box label against this job: ' + (b.partNo ? 'part number <b>' + esc(b.partNo.pn) + '</b>' : 'design label <b>' + esc(b.sku) + '</b> (no part number set yet)') +
          (b.cct ? ', <b>' + esc(b.cct) + '</b>' : '') + '. A different part number, CCT or optic: stop and report it (Material check &rarr; Report a problem).</li>' +
        (b.partNo && b.partNo.parts ? '<li>This part number means: <b>' + esc(b.partNo.parts.means) + '</b>.</li>' : '') +
        voltageNote(b, pins) +
        '<li>Inspect for shipping damage before installing. A damaged fixture is not installed; photograph it and report it.</li>' +
        '<li>Lift and fall protection for the mounting height, cones around the work area, and the store\'s site rules for working in the lot.</li></ol>' +

      '<h2>2 · Make it safe</h2><div class="warn">Electrical work by a qualified electrician, to the NEC and local code.</div><ol>' +
        '<li>Switch off the circuit at the panel, lock it out and tag it.</li>' +
        '<li>Prove it dead at the fixture with a tester you have just checked on a live source.</li>' +
        '<li>Lighting circuits can be fed from more than one breaker or through a contactor or photocell: test every conductor.</li></ol>' +

      '<h2>3 · Remove the old fixture</h2><ol>' +
        '<li>Disconnect and remove the existing fixture' + (mh ? ', its ballast and igniter' : '') + '. Cap and label any conductors left unused.</li>' +
        (mh ? '<li>Metal halide and other HID lamps contain mercury: do not break them, keep them for recycling as universal waste under your state\'s rules.</li>' : '') +
        '<li>Check the pole top or wall surface, the hand hole and the wiring for damage or corrosion. Note anything you find in the pin\'s note.</li></ol>' +

      '<h2>4 · Mount the new fixture</h2><ol>' + mountSteps(kind, b, sol).map(function (x) { return '<li>' + x + '</li>'; }).join('') + '</ol>' +

      '<h2>5 · Wire</h2><ol>' +
        '<li>Connect line, neutral (or the second line on 208/240/480 V) and ground exactly as the wiring label on the fixture shows. Equipment ground is always connected.</li>' +
        '<li>Dimming or control leads that are not used: cap them separately, never to line voltage.</li>' +
        '<li>Fit any photocell, shorting cap or sensor the design calls for. Use wet-location connectors and seal entries.</li></ol>' +

      '<h2>6 · Check and record</h2><ol>' +
        '<li>Restore power and check every head on the pole lights with no flicker.</li>' +
        '<li>In the app, open the pin, take a photo that shows the installed fixture (and its label if you can), and SAVE AS INSTALLED. Every head is its own pin.</li>' +
        '<li>Anything not as designed (different mount, aim, height): write it in the pin\'s note.</li></ol>' +

      '<h2>Where they go</h2><table><tr><th>Tag</th><th>Pole</th><th>Fixture</th></tr>' +
        pins.map(function (p) { return '<tr><td>' + esc(p.tag) + '</td><td>' + esc(p.poleId || '-') + '</td><td>' + esc(p.fid) + '</td></tr>'; }).join('') + '</table>' +
      '<p class="muted" style="margin-top:20px">Questions: ' + esc(d.contact.company) + ' · <a href="tel:' + esc(d.contact.phone.replace(/[^0-9+]/g, '')) + '">' + esc(d.contact.phone) + '</a> · <a href="mailto:' + esc(d.contact.email) + '">' + esc(d.contact.email) + '</a></p>';
    document.getElementById('out').innerHTML = h;
  }

  LCI.me().then(function (me) {
    if (!me) { location.replace('./index.html?next=' + encodeURIComponent(location.pathname.replace(/^.*\//, './') + location.search)); return null; }
    return LCI.api('GET', 'jobs/' + encodeURIComponent(JOB));
  }).then(function (d) { if (d) render(d); })
    .catch(function (e) { document.getElementById('out').innerHTML = '<p class="msg err">' + esc(e.message) + '</p>'; });
})();
