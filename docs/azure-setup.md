# Going live on Azure

Live: https://witty-plant-08257f31e.2.azurestaticapps.net (created 2026-10-20).

Same setup as the customer portal, with the app's own resources and secrets.
Nothing here is in the repo's code; these are clicks in the Azure portal.
tools/azure-setup.ps1 does steps 1 and 3 from the Azure CLI instead.

## 1. Storage container

stled03 > Containers > **+ Container**: name `installer-app`, access level
**Private**.

Then stled03 > Containers > installer-app > Shared access tokens: permissions
Read, Add, Create, Write, Delete, List; expiry as long as you are comfortable
renewing. Copy the **Blob SAS token**. It is scoped to this container only.

Then stled03 > Containers > **customer-portal** > Shared access tokens:
permissions **Read and List only**. Copy that token too: it lets the app read
a project's site (Walmart 2741) and can never change the portal's records.

## 2. Static Web App

Create a resource > Static Web App, resource group `rg_led_dev`, plan Free or
Standard, source GitHub, repo `dinodzevlan02-afk/lc-installer-app`, branch
`main`, build preset **Custom**: app location `/`, API location `api`,
output location empty.

Azure commits its deploy workflow to `.github/workflows/` with the deploy
token as a repository secret. After that, every push to `main` deploys.
The workflow was then given `skip_app_build: true` (plain HTML, as in the
portal) and a smoke-test job that must pass before the deploy.

## 3. App settings (Static Web App > Environment variables)

| Name | Value |
|---|---|
| `INSTALLER_STORAGE_SAS` | the installer-app container SAS from step 1 |
| `INSTALLER_PORTAL_SAS` | the customer-portal READ + LIST SAS from step 1 |
| `INSTALLER_JWT_SECRET` | 32+ random characters, NOT the portal's PORTAL_JWT_SECRET |
| `INSTALLER_SETUP_KEY` | 12+ characters, used once to create the first admin |
| `INSTALLER_PUBLIC_URL` | optional: the custom domain, for invite links |
| `INSTALLER_CONTACT_PHONE` / `INSTALLER_CONTACT_EMAIL` | optional: shown to installers; default 702.847.7680 / dinod@ledconnection.com |
| `INSTALLER_STORAGE_ACCOUNT` / `INSTALLER_CONTAINER` | optional overrides of stled03 / installer-app |

A random secret, for example in PowerShell:
`-join ((48..57)+(65..90)+(97..122) | Get-Random -Count 40 | % {[char]$_})`

## 4. First admin and the first job

Open the site. It shows **First-time Setup** while no admin exists. Enter the
setup key and your login. It works once; after that the page is sign-in only.

Then on the home page: add an installer login (copy the one-time link to
them), and under Jobs open a job with the customer portal's project id for
Walmart 2741 (as in the portal's Projects table), ticking the installer.

## GitHub settings worth switching on

Repository > Settings: Code security > **Secret scanning** and **Push
protection** (blocks a pushed secret); Branches > a rule on `main`
requiring a pull request if more than one person pushes.
