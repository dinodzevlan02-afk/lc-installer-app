/* POST /api/logout  -> clears the session cookie. */
const P = require("../shared/app");

module.exports = P.handler(async ({ send }) => {
  send(200, { ok: true }, { "Set-Cookie": P.A.clearCookie() });
});
