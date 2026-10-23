/* LC Installer App - the pages' one way to talk to /api.
   Copied from lc-customer-portal/lcp.js (2026-10-20).

   The session itself is an HttpOnly cookie the page cannot see; the browser
   sends it on its own. What IS kept in sessionStorage ('lci_me') is only the
   display copy of /api/me (name, role), so a page can draw its header
   without waiting. It grants nothing: every API call is checked on the
   server. */
(function () {
  'use strict';
  var ME_KEY = 'lci_me';

  function api(method, path, body) {
    var opt = { method: method, credentials: 'same-origin', cache: 'no-store', headers: {} };
    if (method !== 'GET') opt.headers['X-LCI'] = '1';
    if (body !== undefined) { opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(body); }
    return fetch('/api/' + path, opt).then(function (r) {
      return r.text().then(function (t) {
        var j = null;
        try { j = t ? JSON.parse(t) : null; } catch (e) { j = null; }
        if (!r.ok) {
          var err = new Error((j && j.error) || ('Request failed (' + r.status + ').'));
          err.status = r.status;
          throw err;
        }
        return j;
      });
    });
  }

  function remember(me) { try { sessionStorage.setItem(ME_KEY, JSON.stringify(me)); } catch (e) {} return me; }
  function forget() { try { sessionStorage.removeItem(ME_KEY); } catch (e) {} }
  function cached() { try { return JSON.parse(sessionStorage.getItem(ME_KEY) || 'null'); } catch (e) { return null; } }

  /* Resolves to /api/me, or null when nobody is signed in. */
  function me() {
    return api('GET', 'me').then(remember, function (e) { if (e.status === 401) { forget(); return null; } throw e; });
  }

  function signOut() {
    forget();
    return api('POST', 'logout').catch(function () {}).then(function () { location.replace('./index.html'); });
  }

  var ROLE_LABEL = { 'lc-admin': 'LED Connection admin', 'installer': 'Installer' };

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* A random temporary password an admin can read out or paste: no
     look-alike characters (0/O, 1/l/I). */
  function tempPassword() {
    var chars = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789', out = '', a = new Uint32Array(14);
    crypto.getRandomValues(a);
    for (var i = 0; i < a.length; i++) { out += chars[a[i] % chars.length]; if (i === 4 || i === 9) out += '-'; }
    return out;
  }

  /* The launcher's PCB circuit traces, drawn behind the page. Same drawing as
     lc-catalog/index.html's #circuit so the two front doors match; styled
     by #circuit rules in lci.css (which also stops it moving for anyone who
     asked their system for reduced motion). */
  var CIRCUIT =
    '<svg id="circuit" viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice" fill="none" aria-hidden="true">' +
    '<g class="tr cy">' +
      '<path class="flow" d="M-40 170 L210 170 L210 320 L300 320 L360 260 L560 260"/>' +
      '<path class="flow s2" d="M420 172 L840 172 L900 232 L1060 232 L1120 292 L1480 292"/>' +
      '<path class="flow s3" d="M1480 150 L1330 150 L1330 300 L1180 300"/>' +
      '<path class="flow s2" d="M-40 470 L120 470 L190 540 L190 690 L300 690"/>' +
      '<path class="flow s3" d="M520 830 L760 830 L830 760 L1010 760"/>' +
      '<path class="flow" d="M1480 640 L1300 640 L1240 580 L1240 460"/></g>' +
    '<g class="tr or">' +
      '<path class="flow s2" d="M-40 730 L150 730 L220 800 L430 800"/>' +
      '<path class="flow s3" d="M1480 812 L1290 812 L1240 762 L1240 700"/>' +
      '<path class="flow" d="M1390 420 L1440 470 L1440 560"/></g>' +
    '<g fill="#22d3ee" class="nd"><circle cx="560" cy="260" r="4"/><circle cx="1180" cy="300" r="4"/>' +
      '<circle cx="300" cy="690" r="4"/><circle cx="1010" cy="760" r="4"/><circle cx="1240" cy="460" r="4"/><circle cx="210" cy="170" r="3"/></g>' +
    '<g fill="#f37021" class="nd"><circle cx="430" cy="800" r="4"/><circle cx="1240" cy="700" r="4"/><circle cx="1390" cy="420" r="3"/></g>' +
    '<g>' +
      '<circle r="3.4" fill="#22d3ee" class="pulse"><animateMotion dur="9s" repeatCount="indefinite" path="M-40 170 L210 170 L210 320 L300 320 L360 260 L560 260"/></circle>' +
      '<circle r="3.4" fill="#22d3ee" class="pulse"><animateMotion dur="12s" repeatCount="indefinite" begin="-4s" path="M420 172 L840 172 L900 232 L1060 232 L1120 292 L1480 292"/></circle>' +
      '<circle r="3.4" fill="#22d3ee" class="pulse"><animateMotion dur="10s" repeatCount="indefinite" begin="-2s" path="M1480 640 L1300 640 L1240 580 L1240 460"/></circle>' +
      '<circle r="3.4" fill="#f37021" class="pulse po"><animateMotion dur="11s" repeatCount="indefinite" begin="-6s" path="M-40 730 L150 730 L220 800 L430 800"/></circle>' +
      '<circle r="3.4" fill="#f37021" class="pulse po"><animateMotion dur="13s" repeatCount="indefinite" begin="-3s" path="M1480 812 L1290 812 L1240 762 L1240 700"/></circle>' +
    '</g></svg>';

  function circuit() {
    if (!document.getElementById('circuit')) document.body.insertAdjacentHTML('afterbegin', CIRCUIT);
  }

  /* BETA strip across the top of every page, as in the customer portal.
     Every page loads this file at the end of <body>, so it is drawn here
     once. Remove the call to take it down. */
  function betaBanner() {
    if (document.getElementById('lciBeta')) return;
    var st = document.createElement('style');
    st.textContent =
      '#lciBeta{position:relative;z-index:5000;flex:none;display:flex;align-items:center;justify-content:center;gap:10px;' +
      'padding:4px 12px;background:linear-gradient(90deg,#f37021,#ff8a3d);color:#111;' +
      "font:600 11px/1.35 'JetBrains Mono',ui-monospace,monospace;letter-spacing:.06em;text-align:center}" +
      '#lciBeta b{background:#111;color:#f37021;padding:1px 7px;border-radius:3px;letter-spacing:.14em}' +
      '@media (max-width:767px){#lciBeta .long{display:none}}' +
      '#lciInstall{font:inherit;font-weight:700;letter-spacing:.1em;padding:1px 9px;border:1px solid #111;border-radius:3px;' +
      'background:#111;color:#22d3ee;cursor:pointer;min-height:0}' +
      '#lciInstall[hidden]{display:none}' +
      '@media (pointer:coarse){#lciInstall{min-height:30px;padding:4px 12px}}' +
      '#lciIosTip{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);z-index:6000;max-width:min(420px,calc(100vw - 32px));' +
      'padding:12px 14px;border:1px solid rgba(34,211,238,.45);border-radius:10px;background:#0f1626;color:#e5e7eb;' +
      "font:500 13px/1.5 'JetBrains Mono',ui-monospace,monospace;box-shadow:0 10px 30px rgba(0,0,0,.5)}" +
      '#lciIosTip b{color:#22d3ee}' +
      '@media print{#lciBeta{display:none}}';
    document.head.appendChild(st);
    var d = document.createElement('div');
    d.id = 'lciBeta';
    d.setAttribute('role', 'note');
    /* Wording: Dino, 2026-10-23 (no "testing", no problems mentioned). */
    d.innerHTML = '<b>BETA</b><span>LED Connection Installer App<span class="long">, early access. New features arrive as we go.</span></span>' +
                  '<button type="button" id="lciInstall" hidden title="Install the Installer App on this device: its own icon and window">INSTALL APP</button>';
    document.body.insertBefore(d, document.body.firstChild);
  }
  betaBanner();

  /* The app installed on the device (Dino, 2026-10-21: "a standalone app,
     like the customer portal"): its own icon (LC + wrench), its own window,
     taskbar / Start / home-screen pins, and app links open in it. The
     banner's INSTALL APP shows only where it can be installed and the page
     is not already running as the app. Edge / Chrome / Android offer the
     install (beforeinstallprompt); an iPad or iPhone has no such prompt, so
     there the button explains Share > Add to Home Screen. */
  var installEvt = null;
  function isInstalled() {
    return !!(window.matchMedia && (matchMedia('(display-mode: standalone)').matches ||
              matchMedia('(display-mode: window-controls-overlay)').matches)) || navigator.standalone === true;
  }
  var IOS = /iP(ad|hone|od)/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  function installBtn() { return document.getElementById('lciInstall'); }
  if (IOS && !isInstalled()) { var ib = installBtn(); if (ib) ib.hidden = false; }
  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    installEvt = e;
    var b = installBtn();
    if (b && !isInstalled()) b.hidden = false;
  });
  window.addEventListener('appinstalled', function () {
    installEvt = null;
    var b = installBtn(); if (b) b.hidden = true;
  });
  document.addEventListener('click', function (e) {
    if (!e.target || e.target.id !== 'lciInstall') return;
    if (installEvt) {
      var ev = installEvt; installEvt = null;
      ev.prompt();
      /* a prompt shows once; the browser offers a fresh one later if it can */
      e.target.hidden = true;
      if (ev.userChoice) ev.userChoice.catch(function () {});
      return;
    }
    if (IOS) {
      var t = document.getElementById('lciIosTip');
      if (t) { t.remove(); return; }
      t = document.createElement('div');
      t.id = 'lciIosTip'; t.setAttribute('role', 'status');
      t.innerHTML = 'To install: tap <b>Share</b> (the square with the arrow), then <b>Add to Home Screen</b>. The app then opens from its LED Connection icon.';
      document.body.appendChild(t);
      setTimeout(function () { if (t.parentNode) t.remove(); }, 12000);
    }
  });

  /* Installable as a standalone tablet app (sw.js). Not on localhost, where
     a cached page would hide the edit just made. */
  if ('serviceWorker' in navigator && !/^(localhost|127\.0\.0\.1)$/.test(location.hostname)) {
    navigator.serviceWorker.register('./sw.js').catch(function () {});
  }

  window.LCI = { api: api, me: me, cached: cached, forget: forget, signOut: signOut, ROLE_LABEL: ROLE_LABEL, esc: esc, tempPassword: tempPassword, circuit: circuit };
})();
