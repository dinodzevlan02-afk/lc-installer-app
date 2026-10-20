/* The page behind the one-time link.

   GET  /api/invite?token=...           -> { username, name, kind } or 404
   POST /api/invite  { token, password } -> sets the password, signs them in.

   Works once: using the link retires it, and bumps the session version so
   any session left over from before a reset ends. No session needed - the
   token is the proof, and it was only ever given to that person. */
const P = require("../shared/app");
const INV = require("../shared/invite");
const { A, ApiError } = P;

const DEAD = "This link has expired or was already used. Ask LED Connection to send a new one.";

module.exports = P.handler(async ({ req, method, body, query, send }) => {
  const token = method === "GET" ? query.token : body.token;
  const found = await INV.lookup(token);
  if (!found) throw new ApiError(404, DEAD);
  const user = found.user;
  if (user.disabled) throw new ApiError(403, "This login has been switched off. Contact LED Connection.");

  if (method === "GET") {
    return send(200, { username: user.username, name: user.name || "", kind: user.invite.kind });
  }

  A.checkPasswordPolicy(body.password);
  user.password = await A.hashPassword(body.password);
  user.mustChangePassword = false;
  user.sessionVersion = (user.sessionVersion || 0) + 1;
  user.failedLogins = 0;
  delete user.lockedUntil;
  delete user.invite;
  user.lastLogin = new Date().toISOString();
  await P.store().put(P.paths.user(user.username), user, { ifMatch: found.etag });
  await INV.retire(found.hash);
  await P.audit(req, user.username, "invite.accept", "user:" + user.username);
  send(200, P.describeMe(user), { "Set-Cookie": A.sessionCookie(A.signSession(user)) });
});
