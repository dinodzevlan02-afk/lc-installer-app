# App icon

The Installer App's icon (Dino, 2026-10-21): the LED Connection logo
(app/lc-logo.png, the same file as the customer portal's) on the dark tile with
the orange frame, and a cyan open-end wrench under it so it reads as the
installer's app next to the portal and the audit app.

`icon.svg` is the source. To rebuild the PNGs in app/ (icon-192, icon-512,
icon-512-maskable with the artwork in the 80% safe zone on a full-bleed tile,
apple-touch-icon-180 full-bleed, favicon-16/32): inline the logo as a data URI,
render at 512 px in a browser (render.js, Playwright with transparent
background), then resize with ImageMagick.
