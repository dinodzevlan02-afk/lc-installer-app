# Test fixtures

`portal/` is laid out like the customer portal's container and is read by
the dev server and smoke test as INSTALLER_PORTAL_LOCAL_STORE.

TEST-SITE-01 is SYNTHETIC: made up to test the reader and the API (two
products, poles, an excluded head, a moved pin, pricing and notes that must
never reach an installer). It is not a site and no number from it means
anything. Real sites (Walmart 2741) are read from the portal's storage and
are not committed here.
