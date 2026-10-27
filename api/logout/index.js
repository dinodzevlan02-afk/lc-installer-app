/* POST /api/logout  -> ends this sign-in on the server, then clears the cookie.
   The session's id goes on the login's endedSessions (kept until the token
   would have expired anyway), so a copy of the cookie stops working at once
   (QA 2026-10-27, M2). Other devices of the same login stay signed in. */
const P = require("../shared/app");

module.exports = P.handler(async ({ req, send }) => {
  const tok = P.A.readCookie(req, P.A.COOKIE);
  const claims = tok && P.A.verifySession(tok);
  if (claims && claims.sid) {
    for (let attempt = 0; attempt < 3; attempt++) {
      const rec = await P.store().get(P.paths.user(claims.sub)).catch(() => null);
      if (!rec) break;
      const now = Math.floor(Date.now() / 1000);
      const ended = (rec.data.endedSessions || []).filter(e => e.exp > now && e.sid !== claims.sid).slice(-49);
      ended.push({ sid: claims.sid, exp: claims.exp });
      try {
        await P.store().put(P.paths.user(claims.sub), Object.assign({}, rec.data, { endedSessions: ended }), { ifMatch: rec.etag });
        break;
      } catch (e) {
        if (e.code !== "CONFLICT") throw e;
      }
    }
  }
  send(200, { ok: true }, { "Set-Cookie": P.A.clearCookie() });
});
