/* POST /api/login  { username, password }  -> me, and the session cookie.

   One message for every failure ("username or password is not correct") and
   the same work for an unknown name as a known one, so the sign-in page does
   not tell a stranger which usernames exist. Five wrong passwords lock that
   login for 15 minutes. */
const P = require("../shared/app");
const { A, ApiError } = P;

const MAX_FAILS = 5, LOCK_MINUTES = 15;
const BAD = "Username or password is not correct.";

module.exports = P.handler(async ({ req, body, send }) => {
  const password = typeof body.password === "string" ? body.password : "";
  let username;
  try { username = P.normUser(body.username); } catch (e) { await A.burnPasswordCheck(password); throw new ApiError(401, BAD); }

  const rec = await P.store().get(P.paths.user(username));
  if (!rec) { await A.burnPasswordCheck(password); throw new ApiError(401, BAD); }
  const user = rec.data;

  if (user.lockedUntil && Date.parse(user.lockedUntil) > Date.now()) {
    await A.burnPasswordCheck(password);
    throw new ApiError(429, "Too many attempts. Try again in a few minutes.");
  }

  if (!(await A.verifyPassword(password, user.password))) {
    user.failedLogins = (user.failedLogins || 0) + 1;
    if (user.failedLogins >= MAX_FAILS) {
      user.lockedUntil = new Date(Date.now() + LOCK_MINUTES * 60000).toISOString();
      user.failedLogins = 0;
      await P.audit(req, null, "login.locked", "user:" + username);
    }
    await P.store().put(P.paths.user(username), user, { ifMatch: rec.etag }).catch(() => {});
    throw new ApiError(401, BAD);
  }

  /* Right password. A disabled login is told so plainly: they have proved
     who they are, and "wrong password" would only send them round in circles. */
  if (user.disabled) throw new ApiError(403, "This login has been switched off. Contact LED Connection.");

  user.failedLogins = 0;
  delete user.lockedUntil;
  user.lastLogin = new Date().toISOString();
  await P.store().put(P.paths.user(username), user, { ifMatch: rec.etag }).catch(() => {});
  await P.audit(req, username, "login", "user:" + username);
  send(200, P.describeMe(user), { "Set-Cookie": A.sessionCookie(A.signSession(user)) });
});
