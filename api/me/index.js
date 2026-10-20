/* GET /api/me  -> who is signed in and which screens to show. 401 if nobody. */
const P = require("../shared/app");

module.exports = P.handler(async ({ req, send }) => {
  const s = await P.requireSession(req);
  send(200, P.describeMe(s.user));
});
