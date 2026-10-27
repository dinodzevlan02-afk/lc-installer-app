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
  var ME = null;             // /api/me: who is signed in
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

  /* A product's documents: installation guide, spec sheet, job sheet, then
     the catalog's own PDFs. The pin card shows them as buttons; the material
     check puts them behind one DOCUMENTS button (openDocs). */
  function docList(b) {
    var out = [], g = b && b.partNo && b.partNo.guide;
    if (!b) return out;
    if (g && g.ready) out.push({ label: 'Installation guide (PDF)', note: g.bracketName || '', url: g.url, primary: true, tab: true });
    if (b.specSheetUrl) out.push({ label: 'Spec sheet', url: b.specSheetUrl, tab: true });
    out.push({ label: 'Job sheet', url: './manual.html?job=' + encodeURIComponent(JOB_ID) + '&p=' + encodeURIComponent(b.key) });
    ((b.catalog && b.catalog.docs) || []).forEach(function (d) { out.push({ label: d.label, url: d.url, tab: true, more: true }); });
    return out;
  }
  function docLink(d, full) {
    return '<a class="btn' + (d.primary ? ' primary' : '') + '"' + (d.tab ? ' target="_blank" rel="noopener"' : '') + ' href="' + esc(d.url) + '">' +
      (full ? '<span>' + esc(d.label) + '</span>' + (d.note ? '<span style="font-weight:600;letter-spacing:.04em;text-transform:none">' + esc(d.note) + '</span>' : '') : esc(d.label)) + '</a>';
  }
  function docButtons(b) {
    return docList(b).map(function (d) { return docLink(d, false); }).join('');
  }
  function openDocs(key) {
    var b = product(key);
    if (!b) return;
    var list = docList(b), main = list.filter(function (d) { return !d.more; }), more = list.filter(function (d) { return d.more; });
    $('dcTitle').textContent = b.name;
    $('dcPn').textContent = b.partNo ? b.partNo.pn : b.sku;
    $('dcBody').innerHTML = (b.partNo && b.partNo.setup ? '<div class="docsetup"><div class="k">SET UP</div>' + esc(b.partNo.setup) + '</div>' : '') +
      '<div class="doclist">' + main.map(function (d) { return docLink(d, true); }).join('') +
      (more.length ? '<div class="k">MORE DOCUMENTS</div>' + more.map(function (d) { return docLink(d, true); }).join('') : '') + '</div>';
    $('ovDocs').hidden = false;
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

  /* The UL-listed part number is what the installer checks on the box; the
     design's own label stays underneath for reference. */
  function partMeaning(x) { return x.means || ''; }

  function partLine(b) {
    if (b.partNo) return '<div class="pn">Part no. <b>' + esc(b.partNo.pn) + '</b></div>' +
      (b.partNo.setup ? '<div class="psku setup"><b>Set up</b> ' + esc(b.partNo.setupShort || b.partNo.setup) + '</div>' : '');
    return '<div class="psku">' + esc(b.sku) + '</div><div class="psku warn-pn">No part number set yet: check the box label against the design.</div>';
  }

  /* LED Connection only: design label -> part number for this job. A saved
     number applies for everyone; without one, the number Dino decided for
     that design label applies (api/shared/parts.js DECIDED). The server
     checks every Optimus number against the order logic. */
  function renderParts() {
    if (!D.parts) { $('partsBox').innerHTML = ''; return; }
    var pending = D.parts.filter(function (r) { return !r.saved && !r.decided; }).length;
    $('partsBox').innerHTML = '<details class="partsbox"' + (pending ? ' open' : '') + '><summary>Part numbers <span class="muted">· LED Connection only · ' +
      (pending ? pending + ' not set' : 'all set') + '</span></summary>' +
      '<table class="sum"><tr><th>Design label</th><th>Tags</th><th>UL-listed part number</th><th></th></tr>' +
      D.parts.map(function (r, i) {
        var val = r.saved ? r.saved.pn : (r.decided || '');
        var st = r.saved ? '<span class="st ok">Saved</span>' : r.decided ? '<span class="st ok">Decided</span>' : '<span class="st todo">Not set</span>';
        return '<tr><td class="mono">' + esc(r.label) + '</td><td>' + esc(r.tags.join(', ')) + '</td>' +
          '<td><input class="mono" data-pi="' + i + '" value="' + esc(val) + '" placeholder="LC-..." spellcheck="false" autocapitalize="characters"></td><td>' + st + '</td></tr>';
      }).join('') + '</table>' +
      '<div class="actions" style="justify-content:flex-start"><button type="button" class="primary" id="btnSaveParts">Save part numbers</button>' +
      '<span class="muted" style="font-size:12px">Decided = the number decided for this design label, already applied. Type a different one and save to change it.</span></div></details>';
    $('btnSaveParts').addEventListener('click', function () {
      var by = {};
      Array.prototype.forEach.call($('partsBox').querySelectorAll('input[data-pi]'), function (inp) {
        var r = D.parts[+inp.getAttribute('data-pi')], v = inp.value.trim();
        if (v !== (r.saved ? r.saved.pn : (r.decided || ''))) by[r.label] = v;
      });
      if (!Object.keys(by).length) { toast('Nothing changed.'); return; }
      this.disabled = true;
      api('PUT', 'parts', { byLabel: by }).then(function () { return api('GET'); }).then(function (d) {
        D.site = d.site; D.parts = d.parts;
        renderParts(); renderMaterial();
        toast('Part numbers saved.');
      }).catch(function (e) { toast(e.message, true); $('btnSaveParts').disabled = false; });
    });
  }

  function renderMaterial() {
    var locked = approved();
    /* The header row only shows on the desktop table (job.html, wide screen
       with a mouse); on a tablet each product is its own card. */
    $('lines').innerHTML = (D.site.bom.length ? '<div class="thead" aria-hidden="true"><span>Product</span><span>Part no. · Set up</span>' +
      '<span>Documents</span><span></span><span>Expected</span><span>Received</span><span>Damaged</span><span>Status</span></div>' : '') +
      D.site.bom.map(function (b) {
      var c = counts[b.key] || {};
      return '<div class="line" data-line="' + esc(b.key) + '">' +
        '<div class="info"><div class="head"><span class="pname">' + esc(b.name) + '</span>' +
          '<span class="chips">' + b.tags.map(function (t) {
            var n = b.tagCounts && b.tagCounts[t];
            return '<span class="chip tag">' + esc(t) + (n && b.tags.length > 1 ? ' &times; ' + n : '') + '</span>';
          }).join('') +
            (b.cct ? '<span class="chip">' + esc(b.cct) + '</span>' : '') + (b.volt ? '<span class="chip">' + esc(b.volt) + '</span>' : '') + '</span>' +
          '<span class="state" data-state="' + esc(b.key) + '">' + lineState(b) + '</span></div><div class="pl"' + (b.partNo && b.partNo.setup ? ' title="' + esc(b.partNo.setup) + '"' : '') + '>' + partLine(b) + '</div></div>' +
        '<button type="button" class="docbtn" data-docs="' + esc(b.key) + '">Documents · ' + docList(b).length + '</button>' +
        '<button type="button" class="rptbtn" data-report="' + esc(b.key) + '">Report</button>' +
        '<div class="counts"><div class="cbox"><div class="cl">Expected</div><div class="expected">' + b.qty + '</div></div>' +
          '<div class="cbox"><div class="cl">Received</div>' + stepper(b.key, 'received', c.received, locked) + '</div>' +
          '<div class="cbox"><div class="cl">Damaged</div>' + stepper(b.key, 'damaged', c.damaged || 0, locked) + '</div></div></div>';
    }).join('') || '<p class="muted">This site has no LC products to install.</p>';

    var a = D.material.approved;
    $('matSigned').innerHTML = !a ? '' :
      '<div class="signed' + (a.short || a.damaged ? ' warn' : '') + '"><b>Signed off</b> by ' + esc(a.byName) + ' on ' + esc(new Date(a.at).toLocaleString()) +
      (a.short || a.damaged ? ' · ' + (a.short ? a.short + ' short ' : '') + (a.damaged ? a.damaged + ' damaged' : '') +
        (D.claims.length ? '' : ' · <b>no claim filed yet</b>: use REPORT on the product.') : ' · everything received.') + '</div>';
    $('btnApprove').hidden = locked;
    $('matLead').hidden = locked;
    renderSummary();
    renderClaims();
    renderMessages();
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
    /* Billie Jo, 2026-10-27: "change 'sign off' to 'proceed to installation'".
       The button counts up as products are counted, then names the next step. */
    var all = n && done === n, btn = $('btnApprove');
    btn.textContent = all ? n + ' / ' + n + ' · Proceed to installation' : 'Checklist ' + done + ' / ' + n;
    btn.classList.toggle('primary', !!all);
    btn.classList.toggle('prog', !all);
    btn.style.setProperty('--done', (n ? Math.round(done / n * 100) : 0) + '%');
  }

  function renderClaims() {
    $('claims').innerHTML = !D.claims.length ? '' : '<h3>Claims</h3>' + D.claims.map(function (c) {
      return '<div class="claim"><span class="ref">' + esc(c.ref) + '</span> · ' + esc(c.kindLabel) + ' · ' + esc(new Date(c.at).toLocaleString()) + ' · ' + esc(c.byName) +
        (c.mail ? ' · <span class="muted">' + (c.mail.sent ? 'emailed' : 'not emailed') + '</span>' : '') +
        (c.lines.length ? '<div class="muted">' + c.lines.map(function (l) {
          return esc(l.name) + ': expected ' + l.expected + (l.received != null ? ', received ' + l.received : '') + (l.damaged ? ', damaged ' + l.damaged : '');
        }).join('<br>') + '</div>' : '') +
        (c.note ? '<div>' + esc(c.note) + '</div>' : '') +
        (c.photos.length ? '<div class="shots">' + c.photos.map(function (p) { return '<img src="' + photoUrl(p) + '" alt="">'; }).join('') + '</div>' : '') + '</div>';
    }).join('');
  }

  /* No phone number or email under the material check (Dino, 2026-10-23:
     "remove here contact number and my emails"). REPORT reaches
     LED Connection's list. */
  /* Desktop (wide screen, mouse): the two steps sit in the top bar, as on the
     canvas's desktop board, so the material table starts higher. Same query
     as the desktop table in job.html. */
  var deskMq = window.matchMedia('(min-width: 1280px) and (hover: hover) and (pointer: fine)');
  function placeSteps() {
    var st = document.querySelector('.steps'), nav = document.querySelector('.nav');
    if (deskMq.matches) nav.insertBefore(st, nav.querySelector('.nav-right'));
    else nav.parentNode.insertBefore(st, nav.nextSibling);
  }
  placeSteps();
  if (deskMq.addEventListener) deskMq.addEventListener('change', placeSteps); else deskMq.addListener(placeSteps);

  $('lines').addEventListener('click', function (e) {
    var t = e.target.closest('[data-docs]');
    if (t) openDocs(t.getAttribute('data-docs'));
    var r = e.target.closest('[data-report]');
    if (r) openClaim(r.getAttribute('data-report'));
  });
  $('dcClose').addEventListener('click', function () { $('ovDocs').hidden = true; });
  $('ovDocs').addEventListener('click', function (e) { if (e.target === this) this.hidden = true; });

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
    var missing = 0;
    $('apBody').innerHTML = '<ul class="ck">' + D.site.bom.map(function (b) {
      var c = counts[b.key] || {}, cls, mk, rs;
      if (c.received == null || c.received === '') { missing++; cls = 'todo'; mk = ''; rs = 'TO COUNT'; }
      else {
        var short = Math.max(0, b.qty - c.received), dmg = c.damaged || 0;
        cls = short || dmg ? 'bad' : 'ok'; mk = short || dmg ? '!' : '&#10003;';
        rs = short || dmg ? [short ? 'SHORT ' + short : '', dmg ? 'DAMAGED ' + dmg : ''].filter(Boolean).join(' · ') : c.received + ' OK';
      }
      return '<li class="' + cls + '"><span class="mk">' + mk + '</span><span class="nm">' + esc(b.name) +
        ' <span class="muted mono">(' + b.qty + ')</span></span><span class="rs">' + rs + '</span></li>';
    }).join('') + '</ul>' +
      (missing ? '<p class="msg err">' + missing + ' product' + (missing === 1 ? ' is' : 's are') + ' not counted yet.</p>' : '') +
      '<p class="muted">Anything short or damaged: proceed with what you have, then REPORT it on the product so LED Connection can send the rest.</p>';
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
      var a = r.material.approved, sent = r.notify && r.notify.sent ? ' LED Connection has been emailed.' : '';
      if (a.short || a.damaged) toast('Signed off.' + sent + ' Report the ' + (a.short ? 'shortage' : 'damage') + ' with REPORT on the product.');
      else { toast('Signed off.' + sent + ' On to the install.'); show('install'); }
    }).catch(function (e) { toast(e.message, true); }).then(function () { $('apSend').disabled = false; });
  });

  /* ── Record a message (Dino, 2026-10-23, on the canvas: "make a record
     ... record a screen ... to LED Connection personnel only") ─────────
     Voice, camera or screen through MediaRecorder at a low bitrate, or a
     recording attached from the device (an iPad cannot record its screen
     in a page: it attaches a screen recording from Photos). Uploaded in
     2 MB parts, then POST messages emails the project's LC list. */
  var REC_MAX = 180, REC_BYTES = 60 * 1024 * 1024, rec = null, recTimer = null;
  function mediaUrl(name) { return '/api/jobs/' + encodeURIComponent(JOB_ID) + '/media/' + encodeURIComponent(name); }
  function clock(s) { s = Math.round(s || 0); return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }
  function canRecord() { return !!(window.MediaRecorder && navigator.mediaDevices && navigator.mediaDevices.getUserMedia); }
  function canScreen() { return !!(window.MediaRecorder && navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia) && !window.matchMedia('(pointer: coarse)').matches; }
  function pickMime(audioOnly) {
    var list = audioOnly ? ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'] : ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm', 'video/mp4'];
    for (var i = 0; i < list.length; i++) if (MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(list[i])) return list[i];
    return '';
  }
  function extOf(type, name) {
    var t = String(type || '') + ' ' + String(name || '').toLowerCase();
    return /webm/.test(t) ? 'webm' : /quicktime|\.mov\b/.test(t) ? 'mov' : /mp4|m4a|aac|\.m4v\b/.test(t) ? 'mp4' : '';
  }
  function stopTracks() { if (rec && rec.stream) rec.stream.getTracks().forEach(function (t) { t.stop(); }); }
  function clearRec() {
    clearInterval(recTimer);
    if (rec && rec.recorder && rec.recorder.state === 'recording') { rec.discard = true; rec.recorder.stop(); }
    stopTracks();
    if (rec && rec.url) URL.revokeObjectURL(rec.url);
    rec = null;
    $('rcStage').hidden = true; $('rcLive').srcObject = null;
    $('rcPlay').hidden = true; $('rcPlay').removeAttribute('src'); $('rcPlay').load();
    $('rcTime').textContent = '0:00'; $('rcTime').classList.remove('on');
    $('rcSend').disabled = true; $('rcInfo').textContent = '';
    Array.prototype.forEach.call($('rcKinds').children, function (b) { b.classList.remove('on'); });
  }
  function showTake(blob, ext, seconds, audio) {
    rec.blob = blob; rec.ext = ext; rec.seconds = seconds;
    rec.url = URL.createObjectURL(blob);
    var v = $('rcPlay');
    v.classList.toggle('audio', !!audio); v.src = rec.url; v.hidden = false;
    $('rcStage').hidden = true;
    var mb = (blob.size / 1048576).toFixed(1) + ' MB';
    $('rcInfo').textContent = (seconds ? clock(seconds) + ' · ' : '') + mb + '. Play it back, then send.';
    $('rcSend').disabled = false;
  }
  function getStream(kind) {
    var md = navigator.mediaDevices;
    if (kind === 'voice') return md.getUserMedia({ audio: true });
    if (kind === 'camera') return md.getUserMedia({ video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }, audio: true });
    /* Screen, with the microphone so the installer can talk it through. */
    return md.getDisplayMedia({ video: true, audio: false }).then(function (scr) {
      return md.getUserMedia({ audio: true }).then(function (mic) {
        return new MediaStream(scr.getVideoTracks().concat(mic.getAudioTracks()));
      }, function () { return scr; });
    });
  }
  Array.prototype.forEach.call(document.querySelectorAll('[data-rec]'), function (b) {
    b.addEventListener('click', function () {
      clearRec();
      $('rcNote').value = '';
      $('rcScreen').hidden = !canScreen();
      Array.prototype.forEach.call($('rcKinds').querySelectorAll('[data-k=voice],[data-k=camera]'), function (x) { x.hidden = !canRecord(); });
      $('rcInfo').textContent = canRecord() ? 'Pick how to record.' : 'This browser cannot record here: attach a recording instead.';
      $('ovRec').hidden = false;
    });
  });
  $('rcKinds').addEventListener('click', function (e) {
    var b = e.target.closest('button[data-k]');
    if (!b) return;
    var kind = b.getAttribute('data-k'), note = $('rcNote').value;
    clearRec(); $('rcNote').value = note;
    b.classList.add('on');
    if (kind === 'file') { rec = { kind: 'file' }; $('rcFile').click(); return; }
    rec = { kind: kind };
    var mine = rec;
    $('rcInfo').textContent = kind === 'screen' ? 'Pick the window or screen to share.' : 'Allow the ' + (kind === 'voice' ? 'microphone' : 'camera and microphone') + ' when asked.';
    getStream(kind).then(function (stream) {
      if (rec !== mine) { stream.getTracks().forEach(function (t) { t.stop(); }); return; }
      rec.stream = stream;
      $('rcStage').classList.toggle('voice', kind === 'voice');
      if (kind !== 'voice') $('rcLive').srcObject = stream;
      $('rcStage').hidden = false;
      $('rcGo').textContent = 'Start recording';
      $('rcInfo').textContent = kind === 'screen' ? 'Sharing. Start recording, talk it through, then stop.' : 'Ready. Start recording, then stop when done.';
      /* Sharing ended from the browser's own bar: stop the recording too. */
      stream.getVideoTracks().forEach(function (t) { t.addEventListener('ended', function () { if (rec === mine && rec.recorder && rec.recorder.state === 'recording') rec.recorder.stop(); }); });
    }).catch(function (err) {
      if (rec === mine) { clearRec(); }
      toast('Could not start the ' + (kind === 'screen' ? 'screen sharing' : kind === 'voice' ? 'microphone' : 'camera') + ': ' + (err && err.message || 'not allowed') + '.', true);
    });
  });
  $('rcGo').addEventListener('click', function () {
    if (!rec || !rec.stream) return;
    if (rec.recorder && rec.recorder.state === 'recording') { rec.recorder.stop(); return; }
    var mine = rec, audio = rec.kind === 'voice', mime = pickMime(audio), chunks = [];
    var opt = { audioBitsPerSecond: 64000 };
    if (!audio) opt.videoBitsPerSecond = 1000000;
    if (mime) opt.mimeType = mime;
    var r;
    try { r = new MediaRecorder(rec.stream, opt); } catch (e) { toast('Recording is not available here: ' + e.message, true); return; }
    rec.recorder = r;
    r.ondataavailable = function (ev) { if (ev.data && ev.data.size) chunks.push(ev.data); };
    r.onstop = function () {
      clearInterval(recTimer);
      $('rcTime').classList.remove('on');
      var secs = (Date.now() - mine.t0) / 1000;
      if (rec !== mine || mine.discard) return;
      stopTracks();
      var type = r.mimeType || mime || (audio ? 'audio/webm' : 'video/webm'), blob = new Blob(chunks, { type: type });
      if (!blob.size) { toast('Nothing was recorded. Try again.', true); clearRec(); return; }
      showTake(blob, extOf(type) || 'webm', secs, audio);
    };
    rec.t0 = Date.now();
    r.start(1000);
    $('rcGo').textContent = 'Stop';
    $('rcTime').classList.add('on');
    recTimer = setInterval(function () {
      var s = (Date.now() - mine.t0) / 1000;
      $('rcTime').textContent = clock(s);
      if (s >= REC_MAX && r.state === 'recording') r.stop();
    }, 250);
  });
  $('rcFile').addEventListener('change', function () {
    var f = this.files && this.files[0];
    this.value = '';
    if (!f || !rec || rec.kind !== 'file') return;
    var ext = extOf(f.type, f.name);
    if (!ext) { toast('Attach a video or a voice memo (MP4, MOV, M4A or WebM).', true); return; }
    if (f.size > REC_BYTES) { toast('That recording is ' + Math.round(f.size / 1048576) + ' MB; the limit is 60 MB. Trim it or record a shorter one.', true); return; }
    showTake(f, ext, 0, /^audio\//.test(f.type));
    $('rcPlay').onloadedmetadata = function () { if (rec && rec.kind === 'file' && isFinite(this.duration)) { rec.seconds = this.duration; $('rcInfo').textContent = clock(this.duration) + ' · ' + (f.size / 1048576).toFixed(1) + ' MB. Play it back, then send.'; } };
  });
  function b64(bytes) {
    var s = '', step = 0x8000;
    for (var i = 0; i < bytes.length; i += step) s += String.fromCharCode.apply(null, bytes.subarray(i, i + step));
    return btoa(s);
  }
  function uploadMedia(blob, ext, progress) {
    return blob.arrayBuffer().then(function (ab) {
      var bytes = new Uint8Array(ab), PART = 2 * 1024 * 1024, parts = Math.max(1, Math.ceil(bytes.length / PART));
      var upload = Array.prototype.map.call(crypto.getRandomValues(new Uint8Array(8)), function (x) { return ('0' + x.toString(16)).slice(-2); }).join('');
      var p = Promise.resolve(), out = null;
      for (var i = 0; i < parts; i++) (function (i) {
        p = p.then(function () {
          progress(i + 1, parts);
          return api('PUT', 'media', { data: b64(bytes.subarray(i * PART, (i + 1) * PART)), kind: ext, part: i, parts: parts, upload: upload });
        }).then(function (r) { if (r && r.name) out = r; });
      })(i);
      return p.then(function () { if (!out) throw new Error('The upload did not finish.'); return out; });
    });
  }
  $('rcSend').addEventListener('click', function () {
    if (!rec || !rec.blob) return;
    var take = rec;
    $('rcSend').disabled = true;
    uploadMedia(take.blob, take.ext, function (i, n) { $('rcInfo').textContent = 'Uploading' + (n > 1 ? ' ' + i + ' / ' + n : '') + '…'; })
      .then(function (m) { $('rcInfo').textContent = 'Sending…'; return api('POST', 'messages', { kind: take.kind, media: m.name, note: $('rcNote').value, seconds: take.seconds || null }); })
      .then(function (r) {
        (D.messages = D.messages || []).unshift(r.message);
        renderMessages();
        clearRec(); $('ovRec').hidden = true;
        var n = r.notify || {};
        toast('Message ' + r.message.ref + (n.sent ? ' sent to LED Connection.' : ' saved. The email did not go out (' + (n.reason || 'not set up') + '); LED Connection still sees it here.'), !n.sent);
      })
      .catch(function (e) { toast(e.message, true); $('rcInfo').textContent = 'Not sent. Try again.'; $('rcSend').disabled = false; });
  });
  $('rcCancel').addEventListener('click', function () { clearRec(); $('ovRec').hidden = true; });
  function renderMessages() {
    var list = D.messages || [];
    var h = !list.length ? '' : '<h3>Messages to LED Connection</h3>' + list.map(function (m) {
      var audio = m.kind === 'voice';
      return '<div class="claim"><span class="ref">' + esc(m.ref) + '</span> · ' + esc(m.kindLabel) + (m.seconds ? ' · ' + clock(m.seconds) : '') +
        ' · ' + esc(new Date(m.at).toLocaleString()) + ' · ' + esc(m.byName) +
        (m.mail ? ' · <span class="muted">' + (m.mail.sent ? 'emailed' : 'not emailed') + '</span>' : '') +
        (m.note ? '<div>' + esc(m.note) + '</div>' : '') +
        '<video class="msgvid' + (audio ? ' audio' : '') + '" controls preload="metadata" playsinline src="' + mediaUrl(m.media) + '"></video></div>';
    }).join('');
    Array.prototype.forEach.call(document.querySelectorAll('.msglist'), function (el) { el.innerHTML = h; });
  }

  /* ── Report a problem ───────────────────────────────────────────── */
  var claimKind = null, claimShots = [];
  function renderClaimShots() {
    $('clShots').innerHTML = claimShots.map(function (p) { return '<img src="' + photoUrl(p) + '" alt="">'; }).join('');
  }
  /* key: REPORT on one product row opens with only that product ticked (and
     listed first); REPORT OTHER PROBLEM ticks every line counted short or
     damaged. */
  function openClaim(key) {
    claimKind = null; claimShots = [];
    var one = key && product(key), bom = D.site.bom.slice();
    if (one) {
      bom.sort(function (a, b) { return (b.key === key) - (a.key === key); });
      var oc = counts[key] || {};
      claimKind = oc.damaged ? 'damaged' : oc.received != null && oc.received !== '' && oc.received < one.qty ? 'shortage' : null;
    }
    $('clTitle').textContent = one ? 'Report a problem: ' + one.name : 'Report a material problem';
    Array.prototype.forEach.call($('clKinds').children, function (b) { b.classList.toggle('on', b.getAttribute('data-k') === claimKind); });
    $('clLines').innerHTML = '<label>Products</label>' + bom.map(function (b) {
      var c = counts[b.key] || {}, problem = one ? b.key === key : (c.received != null && c.received < b.qty) || c.damaged;
      return '<div class="cl-line"><input type="checkbox" data-k="' + esc(b.key) + '"' + (problem ? ' checked' : '') + '>' +
        '<span>' + esc(b.name) + ' <span class="muted mono">(expected ' + b.qty + ')</span></span>' +
        '<input type="number" min="0" placeholder="rcvd" data-r="' + esc(b.key) + '" value="' + (c.received == null ? '' : c.received) + '">' +
        '<input type="number" min="0" placeholder="dmg" data-dm="' + esc(b.key) + '" value="' + (c.damaged || 0) + '"></div>';
    }).join('');
    $('clNote').value = '';
    renderClaimShots();
    $('ovClaim').hidden = false;
  }
  $('btnClaim').addEventListener('click', function () { openClaim(); });
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
      var n = r.notify || {};
      toast('Claim ' + r.claim.ref + ' saved' + (n.sent ? ' and emailed to LED Connection' + (n.others ? ' (+' + n.others + ' on this project)' : '') + (n.attached ? ' with ' + n.attached + ' photo' + (n.attached > 1 ? 's' : '') : '') + '.'
        : '. The email did not go out (' + (n.reason || 'not set up') + '); LED Connection still sees it here. Call if the install is held up.'), !n.sent);
    }).catch(function (e) { toast(e.message, true); }).then(function () { $('clSend').disabled = false; });
  });

  /* ══ 2. Install ═════════════════════════════════════════════════════ */
  function todoPins() { return D.site.pins.filter(function (p) { return !p.off && p.product; }); }
  function isDone(p) { return !!(D.pins[p.id] && D.pins[p.id].installed); }

  function pinStyle(p) {
    var dim = filterTag && p.tag !== filterTag, k = pinScale();
    var col = p.off || !p.product ? '#6b7280' : isDone(p) ? '#22c55e' : '#f37021';
    return { radius: (selected === p.id ? 12 : 9) * k, color: selected === p.id ? '#22d3ee' : '#0a0e1a', weight: selected === p.id ? 4 : 2,
             fillColor: col, fillOpacity: dim ? 0.15 : 0.95, opacity: dim ? 0.25 : 1 };
  }

  /* ── PIN SIZE and MAP OPACITY, as in the customer portal (Dino, 2026-10-20)
     Both are preferences of this tablet, kept in its browser, never on the
     job. Pin size scales pins and tags 50-250%. Map opacity washes the
     aerial to WHITE (the map sits on white), so pins stand out on a dark
     aerial; it never darkens. Both live in one pop-up under the zoom. */
  var PIN_MIN = 50, PIN_MAX = 250, tiles = [];
  function pref(key, dflt, lo, hi) {
    var v = NaN;
    try { v = parseInt(localStorage.getItem(key), 10); } catch (e) {}
    return isFinite(v) ? Math.max(lo, Math.min(hi, v)) : dflt;
  }
  function savePref(key, v) { try { localStorage.setItem(key, String(v)); } catch (e) {} }
  function pinScale() { return pref('lc_installer_pin_size', 100, PIN_MIN, PIN_MAX) / 100; }
  var pinTimer = 0;
  function setPinSize(v) {
    v = Math.max(PIN_MIN, Math.min(PIN_MAX, parseInt(v, 10) || 100));
    savePref('lc_installer_pin_size', v);
    $('pinSizeVal').textContent = v + '%';
    $('map').style.setProperty('--pin', v / 100);
    /* One redraw per 60 ms while dragging; a timer, not a frame callback. */
    if (pinTimer) return;
    pinTimer = setTimeout(function () { pinTimer = 0; restyle(); }, 60);
  }
  function setMapOpacity(v) {
    v = Math.max(10, Math.min(100, parseInt(v, 10) || 100));
    savePref('lc_installer_map_wash', v);
    tiles.forEach(function (t) { t.setOpacity(v / 100); });
    $('mapOpacityVal').textContent = v + '%';
  }
  function toggleMapCtl(open) {
    var w = document.querySelector('.map-ctl');
    if (!w) return;
    var on = open == null ? !w.classList.contains('open') : !!open;
    w.classList.toggle('open', on);
    $('mapCtlBtn').setAttribute('aria-expanded', on ? 'true' : 'false');
  }
  function addMapCtl() {
    var ctl = L.control({ position: 'topleft' });
    ctl.onAdd = function () {
      var w = L.DomUtil.create('div', 'map-ctl'), ps = Math.round(pinScale() * 100), op = pref('lc_installer_map_wash', 100, 10, 100);
      w.innerHTML = '<button type="button" class="map-btn" id="mapCtlBtn" title="Map opacity and pin size" aria-label="Map opacity and pin size" aria-expanded="false">' +
          '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/></svg></button>' +
        '<div class="map-pop">' +
          '<div class="row"><span class="lbl2">MAP OPACITY</span><input type="range" id="mapOpacity" min="10" max="100" step="5" value="' + op + '" aria-label="Map opacity">' +
            '<span class="val" id="mapOpacityVal">' + op + '%</span></div>' +
          '<div class="row"><span class="lbl2">PIN SIZE</span><input type="range" id="pinSize" min="' + PIN_MIN + '" max="' + PIN_MAX + '" step="10" value="' + ps + '" aria-label="Pin and tag size">' +
            '<span class="val" id="pinSizeVal">' + ps + '%</span></div></div>';
      L.DomEvent.disableClickPropagation(w);   // sliding must not drag the map
      L.DomEvent.disableScrollPropagation(w);
      w.querySelector('#mapCtlBtn').addEventListener('click', function () { toggleMapCtl(); });
      w.querySelector('#mapOpacity').addEventListener('input', function () { setMapOpacity(this.value); });
      w.querySelector('#pinSize').addEventListener('input', function () { setPinSize(this.value); });
      return w;
    };
    ctl.addTo(map);
  }

  function initMap() {
    if (map) return;
    map = L.map('map', { maxZoom: 21, zoomSnap: 0.25, zoomDelta: 0.5, attributionControl: false });
    /* Google satellite + labels, as the customer portal, at this tablet's opacity. */
    var op = pref('lc_installer_map_wash', 100, 10, 100) / 100;
    ['s', 'h'].forEach(function (code) {
      tiles.push(L.tileLayer('https://{s}.google.com/vt/lyrs=' + code + '&x={x}&y={y}&z={z}',
        { subdomains: ['mt0', 'mt1', 'mt2', 'mt3'], maxZoom: 21, maxNativeZoom: 20, opacity: op }).addTo(map));
    });
    $('map').style.setProperty('--pin', pinScale());
    addMapCtl();
    map.on('click', function () { toggleMapCtl(false); });   // a tap on the map puts the pop-up away
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
    h += '<dl class="kv"><dt>Install</dt><dd><b>' + esc(p.productName || (b && b.name) || '') + '</b>' +
        (p.partNo ? '<div class="mono pn">Part no. <b>' + esc(p.partNo) + '</b></div>' : '<div class="mono muted">' + esc(sol.sku) + '</div>') + '</dd>' +
      (p.partNo && b && b.partNo && b.partNo.parts ? '<dt>Part no. means</dt><dd>' + esc(partMeaning(b.partNo.parts)) + '</dd>'
        : sol.specific && sol.specific !== sol.sku ? '<dt>Options</dt><dd>' + esc(sol.specific) + '</dd>' : '') +
      (p.partNo && b && b.partNo && b.partNo.setup ? '<dt>Set up</dt><dd>' + esc(b.partNo.setup) + '</dd>' : '') +
      (p.auditTag && p.auditTag !== p.tag ? '<dt>Audit tag</dt><dd>' + esc(p.auditTag) + '</dd>' : '') +
      (sol.mh ? '<dt>Mount height</dt><dd>' + esc(sol.mh) + ' ft</dd>' : '') +
      (sol.arrangement ? '<dt>Arrangement</dt><dd>' + esc(sol.arrangement) + '</dd>' : '') +
      (sol.tilt ? '<dt>Tilt</dt><dd>' + esc(sol.tilt) + '&deg;</dd>' : '') +
      (sol.armLength ? '<dt>Arm</dt><dd>' + esc(sol.armLength) + '</dd>' : '') +
      (p.added ? '<dt>New head</dt><dd>' + esc(p.added) + '</dd>'
        : '<dt>Replaces</dt><dd>' + esc([p.existing.type, p.existing.tech, p.existing.watts ? p.existing.watts + ' W' : ''].filter(Boolean).join(' · ') || '-') + '</dd>') +
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
      '<button type="button" class="bigbtn" data-next>Next to install' + (filterTag ? ' (' + esc(filterTag) + ')' : '') + '</button>' +
      '<button type="button" class="bigbtn danger" data-flag>Flag a problem</button>';
    var mine = (D.flags || []).filter(function (f) { return f.pinId === p.id; });
    if (mine.length) h += '<div style="margin-top:10px">' + mine.map(flagHtml).join('') + '</div>';
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
      toast(installed ? 'Saved: ' + r.pin.tag + ' installed.' + (r.notify && r.notify.sent ? ' LED Connection emailed with the photo.' : '') : 'Marked not installed.');
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
    else if (t.hasAttribute('data-flag')) openFlag(selected);
  });

  /* ── Flag a problem on one fixture (Dino, 2026-10-21): emailed to the
     same list as a claim, with the fixture, the note and the photos. ── */
  var flagPin = null, flagKind = null, flagShots = [];
  function flagHtml(f) {
    return '<div class="claim flag"><span class="ref">' + esc(f.ref) + '</span> · ' + esc(f.kindLabel) + ' · ' + esc(f.tag) + (f.poleId ? ' · pole ' + esc(f.poleId) : '') +
      ' · ' + esc(new Date(f.at).toLocaleString()) + ' · ' + esc(f.byName) +
      (f.mail ? ' · <span class="muted">' + (f.mail.sent ? 'emailed' : 'not emailed') + '</span>' : '') +
      (f.note ? '<div>' + esc(f.note) + '</div>' : '') +
      (f.photos.length ? '<div class="shots">' + f.photos.map(function (n) { return '<img src="' + photoUrl(n) + '" alt="">'; }).join('') + '</div>' : '') + '</div>';
  }
  function renderFlags() {
    var fl = D.flags || [];
    $('flags').innerHTML = !fl.length ? '' : '<h3>Problems flagged</h3>' + fl.map(flagHtml).join('');
  }
  function renderFlagShots() { $('flShots').innerHTML = flagShots.map(function (n) { return '<img src="' + photoUrl(n) + '" alt="">'; }).join(''); }
  function openFlag(pinId) {
    var p = D.site.pins.filter(function (x) { return x.id === pinId; })[0];
    if (!p) return;
    flagPin = pinId; flagKind = null; flagShots = [];
    Array.prototype.forEach.call($('flKinds').children, function (b) { b.classList.remove('on'); });
    $('flSub').textContent = p.tag + (p.poleId ? ' · pole ' + p.poleId : '') + ' · fixture ' + p.fid + '. LED Connection gets it by email with your photos.';
    $('flNote').value = '';
    renderFlagShots();
    $('ovFlag').hidden = false;
  }
  $('flKinds').addEventListener('click', function (e) {
    var b = e.target.closest('button[data-k]');
    if (!b) return;
    flagKind = b.getAttribute('data-k');
    Array.prototype.forEach.call(this.children, function (x) { x.classList.toggle('on', x === b); });
  });
  $('flPhotoBtn').addEventListener('click', function () { $('flPhoto').click(); });
  $('flPhoto').addEventListener('change', function () {
    var files = Array.prototype.slice.call(this.files || [], 0, 6 - flagShots.length);
    this.value = '';
    files.reduce(function (p, f) {
      return p.then(function () { return upload(f).then(function (r) { flagShots.push(r.name); renderFlagShots(); }); });
    }, Promise.resolve()).catch(function (e) { toast(e.message, true); });
  });
  $('flCancel').addEventListener('click', function () { $('ovFlag').hidden = true; });
  $('flSend').addEventListener('click', function () {
    if (!flagKind) { toast('Pick what the problem is first.', true); return; }
    $('flSend').disabled = true;
    api('POST', 'flags', { pinId: flagPin, kind: flagKind, note: $('flNote').value, photos: flagShots }).then(function (r) {
      D.flags = [r.flag].concat(D.flags || []);
      $('ovFlag').hidden = true;
      renderFlags(); renderCard();
      var n = r.notify || {};
      toast('Problem ' + r.flag.ref + ' saved' + (n.sent ? ' and emailed to LED Connection' + (n.others ? ' (+' + n.others + ' on this project)' : '') + '.'
        : '. The email did not go out (' + (n.reason || 'not set up') + '); LED Connection still sees it here.'), !n.sent);
    }).catch(function (e) { toast(e.message, true); }).then(function () { $('flSend').disabled = false; });
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
      renderProgress(); renderCard(); renderApproval();
      toast('Job submitted' + (r.notify && r.notify.sent ? '. LED Connection has been asked to approve it' : '') + '. Thank you.');
    }).catch(function (e) { toast(e.message, true); });
  });

  /* ══ Approval (Dino, 2026-10-21) ════════════════════════════════════
     Submitted -> LED Connection reviews and APPROVES (done) or SENDS BACK
     with a reason (the job opens again). The submit email's REVIEW AND
     APPROVE button lands here with ?review=1. */
  function isLcUser() { return !!(ME && ME.can && ME.can.manageUsers); }
  function renderApproval() {
    var j = D.job, el = $('approval'), h = '', cls = '';
    var openN = (D.claims || []).filter(function (c) { return c.status === 'open'; }).length + (D.flags || []).filter(function (f) { return f.status === 'open'; }).length;
    if (j.accepted) {
      cls = 'done';
      h = '<div class="t"><b>Approved</b> · ' + esc(j.accepted.byName || j.accepted.by) + ' · ' + esc(new Date(j.accepted.at).toLocaleString()) +
        (j.accepted.note ? '<div>' + esc(j.accepted.note) + '</div>' : '') + '</div>';
    } else if (j.submitted) {
      cls = 'wait';
      h = '<div class="t"><b>' + (isLcUser() ? 'Install complete: waiting for your approval' : 'Submitted: waiting for LED Connection to approve') + '</b><div>' +
        j.submitted.heads + ' fixtures, submitted by ' + esc(j.submitted.byName || j.submitted.by) + ' · ' + esc(new Date(j.submitted.at).toLocaleString()) +
        (openN ? ' · <span style="color:#fca5a5">' + openN + ' claim / problem still open</span>' : '') + '</div></div>' +
        (isLcUser() ? '<button type="button" class="danger" data-sendback>Send back</button><button type="button" class="primary" data-accept>Approve</button>' : '');
    } else if (j.sentBack) {
      cls = 'back';
      h = '<div class="t"><b>Sent back by LED Connection</b> · ' + esc(j.sentBack.byName || j.sentBack.by) + ' · ' + esc(new Date(j.sentBack.at).toLocaleString()) +
        '<div>' + esc(j.sentBack.reason) + '</div><div class="muted">Fix it, then submit the job again.</div></div>';
    }
    el.className = 'approval ' + cls;
    el.innerHTML = h;
    el.hidden = !h;
  }
  $('approval').addEventListener('click', function (e) {
    var b = e.target.closest('button');
    if (!b) return;
    if (b.hasAttribute('data-accept')) {
      var note = prompt('Approve this install? It closes the job and emails everyone.\n\nNote (optional):', '');
      if (note === null) return;
      b.disabled = true;
      api('POST', 'accept', { note: note }).then(function (r) {
        D.job = Object.assign(D.job, r.job); renderApproval();
        toast('Approved' + (r.notify && r.notify.sent ? ' and emailed' : '') + '. The job is done.');
      }).catch(function (err) { toast(err.message, true); b.disabled = false; });
    } else if (b.hasAttribute('data-sendback')) {
      var reason = prompt('What needs fixing? The installer gets the job back with this note.', '');
      if (reason === null) return;
      b.disabled = true;
      api('POST', 'sendback', { reason: reason }).then(function (r) {
        D.job = Object.assign(D.job, r.job); renderApproval(); renderProgress(); renderCard();
        toast('Sent back' + (r.notify && r.notify.sent ? ' and emailed' : '') + '.');
      }).catch(function (err) { toast(err.message, true); b.disabled = false; });
    }
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
      initMap(); renderFilters(); renderProgress(); renderCard(); renderFlags();
      setTimeout(function () { map.invalidateSize(); }, 50);
    }
    try { history.replaceState(null, '', '?id=' + encodeURIComponent(JOB_ID) + (which === 'install' ? '#install' : '')); } catch (e) {}
  }
  $('stMaterial').addEventListener('click', function () { show('material'); });
  $('stInstall').addEventListener('click', function () { if (approved()) show('install'); });

  /* ══ Start ══════════════════════════════════════════════════════════ */
  LCI.me().then(function (me) {
    if (!me || me.user.mustChangePassword) { location.replace('./index.html?next=' + encodeURIComponent('./job.html' + location.search + location.hash)); return null; }
    ME = me;
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
    renderParts(); renderMaterial(); renderSteps(); renderApproval();
    var review = /[?&]review=1\b/.test(location.search);
    show(approved() && (review || location.hash === '#install') ? 'install' : 'material');
  }).catch(function (e) {
    $('vLoading').innerHTML = '<p class="msg err">' + esc(e.message) + '</p><p><a href="./home.html">Back to jobs</a></p>';
  });
})();
