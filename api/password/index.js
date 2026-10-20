/* POST /api/password  { current, next }  -> changes your own password.

   Bumps the session version, which signs out every other device, then
   issues this browser a fresh cookie so the person changing it stays in. */
const P = require("../shared/app");
const { A, ApiError } = P;

module.exports = P.handler(async ({ req, body, send }) => {
  const s = await P.requireSession(req);
  if (!(await A.verifyPassword(String(body.current || ""), s.user.password))) throw new ApiError(403, "Current password is not correct.");
  A.checkPasswordPolicy(body.next);
  if (body.next === body.current) throw new ApiError(400, "The new password must be different.");

  const user = s.user;
  user.password = await A.hashPassword(body.next);
  user.sessionVersion = (user.sessionVersion || 0) + 1;
  user.mustChangePassword = false;
  await P.store().put(P.paths.user(user.username), user, { ifMatch: s.etag });
  await P.audit(req, user.username, "password.change", "user:" + user.username);
  send(200, P.describeMe(user), { "Set-Cookie": A.sessionCookie(A.signSession(user)) });
});
