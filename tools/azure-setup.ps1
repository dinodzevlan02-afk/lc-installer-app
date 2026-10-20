<#
  LC Installer App - storage and settings for the Static Web App, in one go.
  OPTIONAL: the same as the Azure portal steps in docs/azure-setup.md. Run on
  your PC, in PowerShell with the Azure CLI (winget install Microsoft.AzureCLI):

      az login
      .\tools\azure-setup.ps1 -AppName <the Static Web App's name>

  The Static Web App itself is created in the Azure portal, linked to GitHub,
  like the customer portal (2026-10-20); this script never creates one.

  What it does (all in resource group rg_led_dev, storage account stled03):
    1. Container `installer-app` (private) for the app's own records.
    2. A container SAS for it (read/add/create/write/delete/list).
    3. A READ-ONLY SAS (read/list) for the customer portal's container, so
       the app can read a project's site (Walmart 2741) and never change it.
    4. App settings on the existing Static Web App: both SAS tokens, a new
       random session secret (never the portal's), a setup key.

  Safe to run again: the container is reused; secrets and SAS tokens are
  issued fresh (a new session secret signs everyone out once).
  The setup key is printed ONCE: you need it on the site's first-time setup.
  This file holds no secrets and is blocked from the live site (/tools/*).
#>
param(
  [string]$ResourceGroup = "rg_led_dev",
  [string]$StorageAccount = "stled03",
  [Parameter(Mandatory = $true)][string]$AppName,
  [int]$SasYears = 2
)
$ErrorActionPreference = "Stop"

function New-Secret([int]$n) {
  $chars = [char[]]"abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
  $bytes = New-Object byte[] $n
  [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
  -join ($bytes | ForEach-Object { $chars[$_ % $chars.Length] })
}

Write-Host "Signed in as:" (az account show --query user.name -o tsv)

# 1. Container
$key = az storage account keys list -g $ResourceGroup -n $StorageAccount --query "[0].value" -o tsv
az storage container create --account-name $StorageAccount --account-key $key --name installer-app --public-access off | Out-Null
Write-Host "Container installer-app ready (private)."

# 2 + 3. SAS tokens
$expiry = (Get-Date).ToUniversalTime().AddYears($SasYears).ToString("yyyy-MM-ddTHH:mmZ")
$ownSas = az storage container generate-sas --account-name $StorageAccount --account-key $key --name installer-app `
  --permissions racwdl --expiry $expiry --https-only -o tsv
$portalSas = az storage container generate-sas --account-name $StorageAccount --account-key $key --name customer-portal `
  --permissions rl --expiry $expiry --https-only -o tsv
Write-Host "SAS tokens issued, valid until $expiry (renew by running this again)."

# The Static Web App must already exist (created in the Azure portal).
$exists = az staticwebapp list -g $ResourceGroup --query "[?name=='$AppName'] | length(@)" -o tsv
if ($exists -eq "0") { throw "No Static Web App '$AppName' in $ResourceGroup. Create it in the Azure portal first (docs/azure-setup.md)." }

# 4. App settings
$setupKey = New-Secret 20
az staticwebapp appsettings set -n $AppName -g $ResourceGroup --setting-names `
  "INSTALLER_STORAGE_SAS=$ownSas" `
  "INSTALLER_PORTAL_SAS=$portalSas" `
  "INSTALLER_JWT_SECRET=$(New-Secret 48)" `
  "INSTALLER_SETUP_KEY=$setupKey" | Out-Null
Write-Host "App settings saved."

$host_ = az staticwebapp show -n $AppName -g $ResourceGroup --query "defaultHostname" -o tsv
Write-Host ""
Write-Host "==== First-time setup key (shown once) ===="
Write-Host $setupKey
Write-Host ""
Write-Host "Site: https://$host_"
