# QA pass (2026-10-27)

Black-box test pass of the Installer App, re-runnable after any change. Not
deployed (tools/ is never published). Each script starts its own dev server
on port 4400 with a throwaway store (`out/store`), an LC admin `dino`, two
crews with one installer each (`alice` on KR-00345-NV, `bob` on TEST-SITE-01).

    python3 tools/qa/c1_security.py    # access control, abuse, validation (API)
    python3 tools/qa/c2_journey.py     # the installer's whole job on an iPad, LC approval bar
    python3 tools/qa/c3_platform.py    # phone / iPad / laptop / desktop: sideways scroll, 44 px, axe-core
    python3 tools/qa/c4_operations.py  # no signal, two tablets, expired session, bad links, upload retry
    python3 tools/qa/c5_phonecard.py   # phone: a picked head gets the panel

Needs Python Playwright with Chromium (`/opt/pw-browsers/chromium` in the
cloud sessions; change `executable_path` in harness.py elsewhere) and Pillow.
Screenshots go to `out/shots/`. Methods: Anthropic's webapp-testing skill,
SFDPOT, OWASP WSTG (authorization, uploads). The findings and fixes are in
CLAUDE.md, "QA pass".
