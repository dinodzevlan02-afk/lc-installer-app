/* GET  /api/setup  -> { needed }        is the first admin still to be made?
   POST /api/setup  { key, username, name, email, password }
        -> creates the first LED Connection admin and signs them in.

   Works exactly once. The key is the INSTALLER_SETUP_KEY app setting, so only
   someone who can see the Azure settings can claim the app; after that,
   system/setup.json exists and this endpoint refuses. Claiming that file is
   a create-only write, so two people racing for it cannot both win. */
const crypto = require("crypto");
const P = require("../shared/app");
const { A, ApiError } = P;

module.exports = P.handler(async ({ req, method, body, send }) => {
  const done = await P.store().get("system/setup.json");
  if (method === "GET") return send(200, { needed: !done });
  if (done) throw new ApiError(409, "Setup has already been completed.");

  const want = process.env.INSTALLER_SETUP_KEY || "";
  if (want.length < 12) throw new ApiError(500, "INSTALLER_SETUP_KEY app setting is not configured (min 12 chars).");
  const got = String(body.key || "");
  const a = crypto.createHash("sha256").update(got).digest(), b = crypto.createHash("sha256").update(want).digest();
  if (!crypto.timingSafeEqual(a, b)) throw new ApiError(403, "Setup key is not correct.");

  const username = P.normUser(body.username);
  A.checkPasswordPolicy(body.password);
  const now = new Date().toISOString();
  const user = {
    username, role: "lc-admin",
    name: P.text(body.name, 100, "Name"), email: P.text(body.email, 200, "Email"),
    password: await A.hashPassword(body.password), sessionVersion: 1,
    disabled: false, mustChangePassword: false, created: now, createdBy: "setup", lastLogin: now
  };

  await P.store().put("system/setup.json", { at: now, by: username }, { ifNoneMatch: "*" });
  await P.store().put(P.paths.user(username), user, { ifNoneMatch: "*" });
  await P.audit(req, username, "setup.first-admin", "user:" + username);
  send(200, P.describeMe(user), { "Set-Cookie": A.sessionCookie(A.signSession(user)) });
});
