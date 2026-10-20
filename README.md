# LC Installer App

LED Connection's app for installers in the field, companion to the customer
portal. Same sign-in and security model as lc-customer-portal, with its own
storage container, cookie and secrets.

- Roles: LED Connection admins, installers.
- Live: https://witty-plant-08257f31e.2.azurestaticapps.net
- Flow: material check (count, claim, sign off) -> install on the satellite map (photo per head) -> submit.
- Data layout: docs/storage.md. Going live: docs/azure-setup.md.

Local (Node 20+, no install):

    node dev/server.js   # http://localhost:4310, setup key local-dev-setup-key
    node dev/smoke.js    # API security checks
