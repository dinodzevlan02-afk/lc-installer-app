/* LC Installer App - the job page (job.html?id=<portal project id>).

   Everything comes from GET /api/jobs/{id} in one call: the site (pins, the
   material list, tags), the material check, saved pins, claims and the
   office contact. Every change goes back through the API, which checks the
   same rules again; this page only decides what to draw. Every value from
   the server is escaped (esc) before it goes into HTML. */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var esc = LCI.esc;
  var JOB_ID = new URLSearchParams(location.search).get('id') || '';
  var D = null;              // the job, as GET /api/jobs/{id} returned it
  var counts = {};           // productKey -> { received, damaged, note }
  var map = null, markers = {}, labels = {}, filterTag = null, selected = null, pinShots = [];

  function api(method, path, body) { return LCI.api(method, 'jobs/' + encodeURIComponent(JOB_ID) + (path ? '/' + path : ''), body); }

  var toastTimer = null;
  function toast(msg, err) {
    var t = document.querySelector('.toast');
    if (!t) { t = document.createElement('div'); t.className = 'toast'; document.body.appendChild(t); }
    t.textContent = msg; t.classList.toggle('err', !!err); t.hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(function () { t.hidden = true; }, err ? 6000 : 2600);
  }

  /* ── Photos: shrunk in the browser like the portal (1600 px, JPEG 0.82) ── */
  function shrink(file) {
    return new Promise(function (resolve, reject) {
      var img = new Image(), url = URL.createObjectURL(file);
      img.onload = function () {
        var k = Math.min(1, 1600 / Math.max(img.naturalWidth, img.naturalHeight));
        var c = document.createElement('canvas');
        c.width = Math.round(img.naturalWidth * k); c.height = Math.round(img.naturalHeight * k);
        c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
        URL.revokeObjectURL(url);
        resolve(c.toDataURL('image/jpeg', 0.82));
      };
      img.onerror = function () { URL.revokeObjectURL(url); reject(new Error('That file is not a photo.')); };
      img.src = url;
    });
  }
  function upload(file) { return shrink(file).then(function (d) { return api('PUT', 'photos', { dataUrl: d }); }); }
  function photoUrl(name) { return '/api/jobs/' + encodeURIComponent(JOB_ID) + '/photos/' + encodeURIComponent(name); }

  function product(key) { return D.site.bom.filter(function (b) { return b.key === key; })[0] || null; }

  /* Spec sheet and manual buttons for a product line. */
  function docButtons(b) {
    if (!b) return '';
    var h = '';
    if (b.specSheetUrl) h += '<a class="btn" target="_blank" rel="noopener" href="' + esc(b.specSheetUrl) + '">Spec sheet</a>';
    h += '<a class="btn" href="./manual.html?job=' + encodeURIComponent(JOB_ID) + '&p=' + encodeURIComponent(b.key) + '">Install guide</a>';
    ((b.catalog && b.catalog.docs) || []).forEach(function (d) {
      h += '<a class="btn" target="_blank" rel="noopener" href="' + esc(d.url) + '">' + esc(d.label) + '</a>';
    });
    return h;
  }

  /* ══ 1. Material check ══════════════════════════════════════════════ */
  function approved() { return !!(D.material && D.material.approved); }

  function lineState(b) {
    var c = counts[b.key] || {};
    if (c.received == null || c.received === '') return '<span class="st todo">Not counted</span>';
    var out = '';
    if (c.received < b.qty) out += '<span class="st short">Short ' + (b.qty - c.received) + '</span>';
    if (c.received > b.qty) out += '<span class="st over">Over ' + (c.received - b.qty) + '</span>';
    if (c.damaged) out += '<span class="st dmg">Damaged ' + c.damaged + '</span>';
    return out || '<span class="st ok">Matches</span>';
  }

  function stepper(key, field, val, locked) {
    return '<div class="stepper"><button type="button" data-k="' + esc(key) + '" data-f="' + field + '" data-d="-1"' + (locked ? ' disabled' : '') + ' aria-label="Less">&minus;</button>' +
      '<input type="number" inputmode="numeric" min="0" step="1" data-k="' + esc(key) + '" data-f="' + field + '" value="' + (val == null ? '' : val) + '"' + (locked ? ' disabled' : '') + '>' +
      '<button type="button" data-k="' + esc(key) + '" data-f="' + field + '" data-d="1"' + (locked ? ' disabled' : '') + ' aria-label="More">+</button></div>';
  }

  function renderMaterial() {
    var locked = approved();
    $('lines').innerHTML = D.site.bom.map(function (b) {
      var c = counts[b.key] || {};
      return '<div class="line" data-line="' + esc(b.key) + '">' +
        '<div><div class="pname">' + esc(b.name) + '</div><div class="psku">' + esc(b.sku) + '</div>' +
          '<div class="chips">' + b.tags.map(function (t) { return '<span class="chip tag">' + esc(t) + '</span>'; }).join('') +
            (b.cct ? '<span class="chip">' + esc(b.cct) + '</span>' : '') + (b.volt ? '<span class="chip">' + esc(b.volt) + '</span>' : '') + '</div>' +
          '<div class="docs">' + docButtons(b) + '</div></div>' +
        '<div class="counts"><div class="cbox"><div class="cl">Expected</div><div class="expected">' + b.qty + '</div></div>' +
          '<div class="cbox"><div class="cl">Received</div>' + stepper(b.key, 'received', c.received, locked) + '</div>' +
          '<div class="cbox"><div class="cl">Damaged</div>' + stepper(b.key, 'damaged', c.damaged || 0, locked) + '</div></div>' +
        '<div class="state" data-state="' + esc(b.key) + '">' + lineState(b) + '</div></div>';
    }).join('') || '<p class="muted">This site has no LC products to install.</p>';

    var a = D.material.approved;
    $('matSigned').innerHTML = !a ? '' :
      '<div class="signed' + (a.short || a.damaged ? ' warn' : '') + '"><b>Signed off</b> by ' + esc(a.byName) + ' on ' + esc(new Date(a.at).toLocaleString()) +
      (a.short || a.damaged ? ' · ' + (a.short ? a.short + ' short ' : '') + (a.damaged ? a.damaged + ' damaged' : '') +
        (D.claims.length ? '' : ' · <b>no claim filed yet</b>: use REPORT A PROBLEM.') : ' · everything received.') + '</div>';
    $('btnApprove').hidden = locked;
    $('matLead').hidden = locked;
    renderSummary();
    renderClaims();
  }

  function renderSummary() {
    var n = D.site.bom.length, done = 0, short = 0, dmg = 0;
    D.site.bom.forEach(function (b) {
      var c = counts[b.key] || {};
      if (c.received != null && c.received !== '') { done++; short += Math.max(0, b.qty - c.received); }
      dmg += c.damaged || 0;
    });
    $('matSum').innerHTML = done + ' of ' + n + ' products counted' + (short ? ' · <span style="color:#fca5a5">' + short + ' short</span>' : '') +
      (dmg ? ' · <span style="color:#fca5a5">' + dmg + ' damaged</span>' : '');
  }

  function renderClaims() {
    $('claims').innerHTML = !D.claims.length ? '' : '<h3>Claims</h3>' + D.claims.map(function (c) {
      return '<div class="claim"><span class="ref">' + esc(c.ref) + '</span> · ' + esc(c.kindLabel) + ' · ' + esc(new Date(c.at).toLocaleString()) + ' · ' + esc(c.byName) +
        (c.lines.length ? '<div class="muted">' + c.lines.map(function (l) {
          return esc(l.name) + ': expected ' + l.expected + (l.received != null ? ', received ' + l.received : '') + (l.damaged ? ', damaged ' + l.damaged : '');
        }).join('<br>') + '</div>' : '') +
        (c.note ? '<div>' + esc(c.note) + '</div>' : '') +
        (c.photos.length ? '<div class="shots">' + c.photos.map(function (p) { return '<img src="' + photoUrl(p) + '" alt="">'; }).join('') + '</div>' : '') + '</div>';
    }).join('');
  }

  function renderContact() {
    var c = D.contact, subj = encodeURIComponent('Installer: ' + D.job.name + ' (' + D.job.id + ')');
    $('contact').innerHTML = '<b>Missing or damaged material?</b> ' + esc(c.company) +
      ' · <a href="tel:' + esc(c.phone.replace(/[^0-9+]/g, '')) + '">' + esc(c.phone) + '</a>' +
      ' · <a href="mailto:' + esc(c.email) + '?subject=' + subj + '">' + esc(c.email) + '</a>';
  }

  /* Counts save themselves a moment after the last change. */
  var saveTimer = null, saving = Promise.resolve();
  function queueSave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(function () {
      saving = saving.then(function () {
        return api('PUT', 'material', { lines: counts }).then(function (r) { D.material = r.material; },
          function (e) { toast(e.message, true); });
      });
    }, 600);
  }

  function setCount(key, field, v) {
    var b = product(key);
    if (!b) return;
    var c = counts[key] = counts[key] || { received: null, damaged: 0, note: '' };
    v = v === '' || v == null ? (field === 'received' ? null : 0) : Math.max(0, Math.floor(Number(v)) || 0);
    c[field] = v;
    if (c.received != null && c.damaged > c.received) c.damaged = c.received;
    var line = document.querySelector('[data-line="' + CSS.escape(key) + '"]');
    if (line) {
      line.querySelector('input[data-f="received"]').value = c.received == null ? '' : c.received;
      line.querySelector('input[data-f="damaged"]').value = c.damaged || 0;
      line.querySelector('[data-state]').innerHTML = lineState(b);
    }
    renderSummary();
    queueSave();
  }

  $('lines').addEventListener('click', function (e) {
    var btn = e.target.closest('button[data-d]');
    if (!btn) return;
    var key = btn.getAttribute('data-k'), f = btn.getAttribute('data-f'), c = counts[key] || {};
    var cur = f === 'received' ? (c.received == null ? product(key).qty : c.received) : (c.damaged || 0);
    /* First tap on an uncounted line starts from the expected quantity. */
    if (f === 'received' && c.received == null) setCount(key, f, cur);
    else setCount(key, f, cur + Number(btn.getAttribute('data-d')));
  });
  $('lines').addEventListener('change', function (e) {
    var i = e.target.closest('input[data-f]');
    if (i) setCount(i.getAttribute('data-k'), i.getAttribute('data-f'), i.value);
  });

  /* Sign off */
  $('btnApprove').addEventListener('click', function () {
    var rows = D.site.bom.map(function (b) {
      var c = counts[b.key] || {};
      return '<tr><td>' + esc(b.name) + '</td><td>' + b.qty + '</td><td>' + (c.received == null ? '<b style="color:#fca5a5">?</b>' : c.received) +
        '</td><td>' + (c.damaged || 0) + '</td></tr>';
    }).join('');
    var missing = D.site.bom.filter(function (b) { return !counts[b.key] || counts[b.key].received == null; }).length;
    $('apBody').innerHTML = '<table class="sum"><tr><th>Product</th><th>Expected</th><th>Received</th><th>Damaged</th></tr>' + rows + '</table>' +
      (missing ? '<p class="msg err">' + missing + ' product' + (missing === 1 ? ' is' : 's are') + ' not counted yet.</p>' : '') +
      '<p class="muted">Anything short or damaged: sign off what you have, then REPORT A PROBLEM so LED Connection can send the rest.</p>';
    $('apConfirm').checked = false;
    $('apSend').disabled = !!missing;
    $('ovApprove').hidden = false;
  });
  $('apCancel').addEventListener('click', function () { $('ovApprove').hidden = true; });
  $('apSend').addEventListener('click', function () {
    if (!$('apConfirm').checked) { toast('Tick the box to confirm you counted the material.', true); return; }
    $('apSend').disabled = true;
    clearTimeout(saveTimer);
    saving.then(function () { return api('POST', 'approve', { lines: counts, confirm: true }); }).then(function (r) {
      D.material = r.material;
      $('ovApprove').hidden = true;
      renderMaterial();
      renderSteps();
      var a = r.material.approved;
      if (a.short || a.damaged) toast('Signed off. Report the ' + (a.short ? 'shortage' : 'damage') + ' with REPORT A PROBLEM.');
      else { toast('Signed off. On to the install.'); show('install'); }
    }).catch(function (e) { toast(e.message, true); }).then(function () { $('apSend').disabled = false; });
  });

  /* ── Report a problem ───────────────────────────────────────────── */
  var claimKind = null, claimShots = [];
  function renderClaimShots() {
    $('clShots').innerHTML = claimShots.map(function (p) { return '<img src="' + photoUrl(p) + '" alt="">'; }).join('');
  }
  $('btnClaim').addEventListener('click', function () {
    claimKind = null; claimShots = [];
    Array.prototype.forEach.call($('clKinds').children, function (b) { b.classList.remove('on'); });
    $('clLines').innerHTML = '<label>Products</label>' + D.site.bom.map(function (b) {
      var c = counts[b.key] || {}, problem = (c.received != null && c.received < b.qty) || c.damaged;
      return '<div class="cl-line"><input type="checkbox" data-k="' + esc(b.key) + '"' + (problem ? ' checked' : '') + '>' +
        '<span>' + esc(b.name) + ' <span class="muted mono">(expected ' + b.qty + ')</span></span>' +
        '<input type="number" min="0" placeholder="rcvd" data-r="' + esc(b.key) + '" value="' + (c.received == null ? '' : c.received) + '">' +
        '<input type="number" min="0" placeholder="dmg" data-dm="' + esc(b.key) + '" value="' + (c.damaged || 0) + '"></div>';
    }).join('');
    $('clNote').value = '';
    renderClaimShots();
    $('ovClaim').hidden = false;
  });
  $('clKinds').addEventListener('click', function (e) {
    var b = e.target.closest('button[data-k]');
    if (!b) return;
    claimKind = b.getAttribute('data-k');
    Array.prototype.forEach.call(this.children, function (x) { x.classList.toggle('on', x === b); });
  });
  $('clPhotoBtn').addEventListener('click', function () { $('clPhoto').click(); });
  $('clPhoto').addEventListener('change', function () {
    var files = Array.prototype.slice.call(this.files || [], 0, 6 - claimShots.length);
    this.value = '';
    files.reduce(function (p, f) {
      return p.then(function () { return upload(f).then(function (r) { claimShots.push(r.name); renderClaimShots(); }); });
    }, Promise.resolve()).catch(function (e) { toast(e.message, true); });
  });
  $('clCancel').addEventListener('click', function () { $('ovClaim').hidden = true; });
  $('clSend').addEventListener('click', function () {
    if (!claimKind) { toast('Pick what is wrong first.', true); return; }
    var lines = [];
    Array.prototype.forEach.call($('clLines').querySelectorAll('input[type=checkbox]:checked'), function (cb) {
      var k = cb.getAttribute('data-k');
      lines.push({ key: k, received: document.querySelector('[data-r="' + CSS.escape(k) + '"]').value,
                   damaged: document.querySelector('[data-dm="' + CSS.escape(k) + '"]').value });
    });
    $('clSend').disabled = true;
    api('POST', 'claims', { kind: claimKind, lines: lines, note: $('clNote').value, photos: claimShots }).then(function (r) {
      D.claims.unshift(r.claim);
      $('ovClaim').hidden = true;
      renderMaterial();
      toast('Claim ' + r.claim.ref + ' sent to LED Connection.');
    }).catch(function (e) { toast(e.message, true); }).then(function () { $('clSend').disabled = false; });
  });

  /* ══ 2. Install ═════════════════════════════════════════════════════ */
  function todoPins() { return D.site.pins.filter(function (p) { return !p.off && p.product; }); }
  function isDone(p) { return !!(D.pins[p.id] && D.pins[p.id].installed); }

  function pinStyle(p) {
    var dim = filterTag && p.tag !== filterTag;
    var col = p.off || !p.product ? '#6b7280' : isDone(p) ? '#22c55e' : '#f37021';
    return { radius: selected === p.id ? 12 : 9, color: selected === p.id ? '#22d3ee' : '#0a0e1a', weight: selected === p.id ? 4 : 2,
             fillColor: col, fillOpacity: dim ? 0.15 : 0.95, opacity: dim ? 0.25 : 1 };
  }

  function initMap() {
    if (map) return;
    map = L.map('map', { maxZoom: 21, zoomSnap: 0.25, zoomDelta: 0.5, attributionControl: false });
    /* Google satellite + labels, as the customer portal. */
    ['s', 'h'].forEach(function (code) {
      L.tileLayer('https://{s}.google.com/vt/lyrs=' + code + '&x={x}&y={y}&z={z}',
        { subdomains: ['mt0', 'mt1', 'mt2', 'mt3'], maxZoom: 21, maxNativeZoom: 20 }).addTo(map);
    });
    var pts = [];
    D.site.pins.forEach(function (p) {
      if (p.lat == null || p.lng == null) return;
      pts.push([p.lat, p.lng]);
      markers[p.id] = L.circleMarker([p.lat, p.lng], pinStyle(p)).addTo(map).on('click', function () { pick(p.id, false); });
    });
    if (pts.length) map.fitBounds(pts, { padding: [50, 50], maxZoom: 19 }); else map.setView([39.5, -98.35], 4);
    map.on('zoomend', renderLabels);
    renderLabels();
  }

  /* Tag labels when zoomed in, or on the filtered tag. */
  function renderLabels() {
    if (!map) return;
    var show = map.getZoom() >= 19;
    D.site.pins.forEach(function (p) {
      var want = markers[p.id] && (show || (filterTag && p.tag === filterTag)) && (!filterTag || p.tag === filterTag);
      if (want && !labels[p.id]) {
        labels[p.id] = L.marker([p.lat, p.lng], { interactive: false, keyboard: false,
          icon: L.divIcon({ className: 'lbl-wrap', html: '<span class="lbl">' + esc(p.tag) + '</span>', iconSize: [0, 0] }) }).addTo(map);
      } else if (!want && labels[p.id]) { map.removeLayer(labels[p.id]); delete labels[p.id]; }
    });
  }

  function restyle() { D.site.pins.forEach(function (p) { if (markers[p.id]) markers[p.id].setStyle(pinStyle(p)); }); }

  function renderProgress() {
    var all = todoPins(), done = all.filter(isDone).length;
    $('progBig').innerHTML = done + ' / ' + all.length + ' <small>INSTALLED</small>';
    $('progBar').style.width = (all.length ? 100 * done / all.length : 0) + '%';
    $('btnSubmit').disabled = !all.length || done < all.length || !!D.job.submitted;
    $('btnSubmit').textContent = D.job.submitted ? 'Submitted ' + new Date(D.job.submitted.at).toLocaleDateString() : 'Submit job';
  }

  function renderFilters() {
    var all = todoPins();
    var h = '<button type="button" class="flt' + (!filterTag ? ' on' : '') + '" data-t="">All <span class="c">' + all.filter(isDone).length + '/' + all.length + '</span></button>';
    D.site.tags.forEach(function (t) {
      var ps = all.filter(function (p) { return p.tag === t.tag; });
      h += '<button type="button" class="flt' + (filterTag === t.tag ? ' on' : '') + '" data-t="' + esc(t.tag) + '">' + esc(t.tag) +
        ' <span class="c">' + ps.filter(isDone).length + '/' + ps.length + '</span></button>';
    });
    $('filters').innerHTML = h;
  }

  $('filters').addEventListener('click', function (e) {
    var b = e.target.closest('button[data-t]');
    if (!b) return;
    filterTag = b.getAttribute('data-t') || null;
    renderFilters(); restyle(); renderLabels();
    var ps = D.site.pins.filter(function (p) { return markers[p.id] && (!filterTag || p.tag === filterTag); });
    if (ps.length) map.fitBounds(ps.map(function (p) { return [p.lat, p.lng]; }), { padding: [60, 60], maxZoom: 20 });
    if (filterTag && !selected) renderTagCard();
  });

  /* Picking a tag with no pin chosen: what that tag is and how many. */
  function renderTagCard() {
    var ps = todoPins().filter(function (p) { return p.tag === filterTag; });
    var b = ps[0] && product(ps[0].productKey);
    $('card').innerHTML = '<h2>' + esc(filterTag) + '</h2><div class="sub">' + ps.length + ' fixture' + (ps.length === 1 ? '' : 's') +
      ' · ' + ps.filter(isDone).length + ' installed</div>' +
      (b ? '<dl class="kv"><dt>Product</dt><dd><b>' + esc(b.name) + '</b><div class="mono muted">' + esc(b.sku) + '</div></dd></dl><div class="docs">' + docButtons(b) + '</div>' : '') +
      '<button type="button" class="primary bigbtn" data-next>Go to the next one to install</button>';
  }

  function pick(id, pan) {
    selected = id;
    pinShots = (D.pins[id] && D.pins[id].photos || []).slice();
    restyle();
    var p = D.site.pins.filter(function (x) { return x.id === id; })[0];
    if (pan && p && map) map.setView([p.lat, p.lng], Math.max(map.getZoom(), 20));
    renderCard();
  }

  function renderCard() {
    var p = D.site.pins.filter(function (x) { return x.id === selected; })[0];
    if (!p) { $('card').innerHTML = '<p class="empty">Tap a pin on the map, or pick a tag to see where it goes.</p>'; return; }
    var b = p.productKey ? product(p.productKey) : null, rec = D.pins[p.id], sol = p.product || {};
    var pole = p.poleId ? D.site.pins.filter(function (x) { return x.poleId === p.poleId && !x.off && x.product; }) : [];
    var h = '<h2>' + esc(p.tag) + '</h2><div class="sub">' + (p.poleId ? 'Pole ' + esc(p.poleId) + ' · ' : '') + 'Fixture ' + esc(p.fid) + '</div>';
    if (pole.length > 1) {
      h += '<div class="pole">' + pole.map(function (x, i) {
        return '<button type="button" class="small' + (x.id === p.id ? ' cur' : '') + (isDone(x) ? ' done' : '') + '" data-pick="' + esc(x.id) + '">Head ' + (i + 1) + (isDone(x) ? ' ✓' : '') + '</button>';
      }).join('') + '</div>';
    }
    if (p.off) {
      $('card').innerHTML = h + '<p class="msg err">Not replaced in this design' + (p.offReason ? ': ' + esc(p.offReason) : '') + '. Leave it as it is.</p>';
      return;
    }
    h += '<dl class="kv"><dt>Install</dt><dd><b>' + esc(p.productName || (b && b.name) || '') + '</b><div class="mono muted">' + esc(sol.sku) + '</div></dd>' +
      (sol.specific ? '<dt>Options</dt><dd>' + esc(sol.specific) + '</dd>' : '') +
      (sol.designTag && sol.designTag !== p.tag ? '<dt>Design tag</dt><dd>' + esc(sol.designTag) + '</dd>' : '') +
      (sol.mh ? '<dt>Mount height</dt><dd>' + esc(sol.mh) + ' ft</dd>' : '') +
      (sol.arrangement ? '<dt>Arrangement</dt><dd>' + esc(sol.arrangement) + '</dd>' : '') +
      (sol.tilt ? '<dt>Tilt</dt><dd>' + esc(sol.tilt) + '&deg;</dd>' : '') +
      (sol.armLength ? '<dt>Arm</dt><dd>' + esc(sol.armLength) + '</dd>' : '') +
      '<dt>Replaces</dt><dd>' + esc([p.existing.type, p.existing.tech, p.existing.watts ? p.existing.watts + ' W' : ''].filter(Boolean).join(' · ') || '-') + '</dd>' +
      (p.existing.voltage ? '<dt>Site voltage</dt><dd>' + esc(p.existing.voltage) + '</dd>' : '') + '</dl>' +
      '<div class="docs">' + docButtons(b) + '</div>';
    if (rec && rec.installed) h += '<div class="installed"><b>Installed</b> by ' + esc(rec.byName) + ' · ' + esc(new Date(rec.at).toLocaleString()) + '</div>';
    var locked = !!D.job.submitted;
    h += '<label>Photo of the installed fixture</label><div class="shots">' + pinShots.map(function (n) { return '<img src="' + photoUrl(n) + '" alt="">'; }).join('') + '</div>' +
      (locked ? '' : '<button type="button" class="bigbtn" data-shot>' + (pinShots.length ? 'Add another photo' : 'Take photo') + '</button>' +
      '<label for="pinSerial">Serial / date code (optional)</label><input id="pinSerial" maxlength="100" value="' + esc(rec && rec.serial || '') + '">' +
      '<label for="pinNote">Note (optional)</label><textarea id="pinNote" rows="2" maxlength="1000">' + esc(rec && rec.note || '') + '</textarea>' +
      '<button type="button" class="primary bigbtn" data-save' + (pinShots.length ? '' : ' disabled') + '>' + (rec && rec.installed ? 'Update' : 'Save as installed') + '</button>' +
      (rec && rec.installed ? '<button type="button" class="bigbtn" data-undo>Mark not installed</button>' : '')) +
      '<button type="button" class="bigbtn" data-next>Next to install' + (filterTag ? ' (' + esc(filterTag) + ')' : '') + '</button>';
    $('card').innerHTML = h;
  }

  function nextPin() {
    var cur = D.site.pins.filter(function (x) { return x.id === selected; })[0];
    var left = todoPins().filter(function (p) { return !isDone(p) && (!filterTag || p.tag === filterTag) && p.id !== selected && markers[p.id]; });
    if (!left.length) { toast(filterTag ? 'Every ' + filterTag + ' is installed.' : 'Every fixture is installed.'); return; }
    /* The same pole first, then the nearest. */
    if (cur && cur.poleId) {
      var same = left.filter(function (p) { return p.poleId === cur.poleId; });
      if (same.length) return pick(same[0].id, true);
    }
    if (cur) left.sort(function (a, b) {
      return Math.pow(a.lat - cur.lat, 2) + Math.pow(a.lng - cur.lng, 2) - Math.pow(b.lat - cur.lat, 2) - Math.pow(b.lng - cur.lng, 2);
    });
    pick(left[0].id, true);
  }

  function savePin(installed) {
    var id = selected;
    var body = { installed: installed, photos: pinShots, serial: $('pinSerial') ? $('pinSerial').value : '', note: $('pinNote') ? $('pinNote').value : '' };
    return api('PUT', 'pins/' + id, body).then(function (r) {
      D.pins[id] = r.pin;
      restyle(); renderFilters(); renderProgress(); renderCard();
      toast(installed ? 'Saved: ' + r.pin.tag + ' installed.' : 'Marked not installed.');
    }).catch(function (e) { toast(e.message, true); });
  }

  $('card').addEventListener('click', function (e) {
    var t = e.target.closest('button');
    if (!t) return;
    if (t.hasAttribute('data-pick')) pick(t.getAttribute('data-pick'), true);
    else if (t.hasAttribute('data-shot')) $('pinPhoto').click();
    else if (t.hasAttribute('data-save')) { t.disabled = true; savePin(true).then(function () { if (t.isConnected) t.disabled = false; }); }
    else if (t.hasAttribute('data-undo')) savePin(false);
    else if (t.hasAttribute('data-next')) nextPin();
  });
  $('pinPhoto').addEventListener('change', function () {
    var f = this.files && this.files[0];
    this.value = '';
    if (!f || !selected) return;
    var forPin = selected;
    toast('Uploading photo…');
    upload(f).then(function (r) {
      toast('Photo added. Save to record it.');
      if (selected !== forPin) return;
      pinShots.push(r.name);
      renderCard();
    }).catch(function (e) { toast(e.message, true); });
  });

  $('btnSubmit').addEventListener('click', function () {
    if (!confirm('Submit this job to LED Connection? Every fixture is saved as installed.')) return;
    api('POST', 'submit').then(function (r) {
      D.job = Object.assign(D.job, r.job);
      renderProgress(); renderCard();
      toast('Job submitted. Thank you.');
    }).catch(function (e) { toast(e.message, true); });
  });

  /* ══ Steps ══════════════════════════════════════════════════════════ */
  function renderSteps() {
    $('stMaterial').classList.toggle('done', approved());
    $('stInstall').disabled = !approved();
    $('stInstall').classList.toggle('done', !!D.job.submitted);
  }
  function show(which) {
    $('vMaterial').hidden = which !== 'material';
    $('vInstall').hidden = which !== 'install';
    $('stMaterial').classList.toggle('on', which === 'material');
    $('stInstall').classList.toggle('on', which === 'install');
    if (which === 'install') {
      initMap(); renderFilters(); renderProgress(); renderCard();
      setTimeout(function () { map.invalidateSize(); }, 50);
    }
    try { history.replaceState(null, '', '?id=' + encodeURIComponent(JOB_ID) + (which === 'install' ? '#install' : '')); } catch (e) {}
  }
  $('stMaterial').addEventListener('click', function () { show('material'); });
  $('stInstall').addEventListener('click', function () { if (approved()) show('install'); });

  /* ══ Start ══════════════════════════════════════════════════════════ */
  LCI.me().then(function (me) {
    if (!me || me.user.mustChangePassword) { location.replace('./index.html?next=' + encodeURIComponent('./job.html?id=' + JOB_ID)); return null; }
    $('who').innerHTML = '<b>' + esc(me.user.name || me.user.username) + '</b>';
    return api('GET');
  }).then(function (d) {
    if (!d) return;
    D = d;
    counts = JSON.parse(JSON.stringify(d.material.lines || {}));
    document.title = d.job.name + ' - LC Installer';
    $('jobName').textContent = d.job.name;
    $('jobAddr').textContent = d.job.address || d.job.id;
    $('vLoading').hidden = true;
    renderContact(); renderMaterial(); renderSteps();
    show(approved() && location.hash === '#install' ? 'install' : 'material');
  }).catch(function (e) {
    $('vLoading').innerHTML = '<p class="msg err">' + esc(e.message) + '</p><p><a href="./home.html">Back to jobs</a></p>';
  });
})();
