# Going live on Azure

Same setup as the customer portal, with the app's own resources and secrets.
Nothing here is in the repo's code; these are clicks in the Azure portal.

## 1. Storage container

stled03 > Containers > **+ Container**: name `installer-app`, access level
**Private**.

Then stled03 > Containers > installer-app > Shared access tokens: permissions
Read, Add, Create, Write, Delete, List; expiry as long as you are comfortable
renewing. Copy the **Blob SAS token**. It is scoped to this container only,
so it cannot read or touch the portal's records.

## 2. Static Web App

Create a resource > Static Web App, resource group `rg_led_dev`, plan Free or
Standard, source GitHub, repo `dinodzevlan02-afk/lc-installer-app`, branch
`main`, build preset **Custom**: app location `/`, API location `api`,
output location empty.

Azure commits its deploy workflow to `.github/workflows/` with the deploy
token as a repository secret. After that, every push to `main` deploys.
Add `skip_app_build: true` to the workflow's `with:` block, as in the
portal (plain HTML, nothing to build).

## 3. App settings (Static Web App > Environment variables)

| Name | Value |
|---|---|
| `INSTALLER_STORAGE_SAS` | the container SAS from step 1 |
| `INSTALLER_JWT_SECRET` | 32+ random characters, NOT the portal's PORTAL_JWT_SECRET |
| `INSTALLER_SETUP_KEY` | 12+ characters, used once to create the first admin |
| `INSTALLER_PUBLIC_URL` | optional: the custom domain, for invite links |
| `INSTALLER_STORAGE_ACCOUNT` / `INSTALLER_CONTAINER` | optional overrides of stled03 / installer-app |

A random secret, for example in PowerShell:
`-join ((48..57)+(65..90)+(97..122) | Get-Random -Count 40 | % {[char]$_})`

## 4. First admin

Open the site. It shows **First-time Setup** while no admin exists. Enter the
setup key and your login. It works once; after that the page is sign-in only.

## GitHub settings worth switching on

Repository > Settings: Code security > **Secret scanning** and **Push
protection** (blocks a pushed secret); Branches > a rule on `main`
requiring a pull request if more than one person pushes.
