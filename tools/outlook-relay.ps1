<#
  LC Installer App - Outlook relay. A copy of lc-customer-portal's
  tools/outlook-relay.ps1 (2026-10-14) for this app (2026-10-21): its own
  URL, its own key, its own folder and lock, so it runs beside the portal's
  relay. Keep the two in step.

  Sends the installer app's queued emails (material claims) through Dino's
  own Outlook on this PC, so they go out from dinod@ledconnection.com
  straight away, with Dino on BCC, and sit in his Sent Items.

    -Once   one round and exit (testing)
    (none)  keep running, a round every $Every seconds (the scheduled task)

  Key: %USERPROFILE%\.lc-installer-relay\key.txt, the key the installer
  app showed once under EMAIL > PAIR OUTLOOK RELAY. Never commit it.
  Log: %USERPROFILE%\.lc-installer-relay\relay.log
  Ledger: %USERPROFILE%\.lc-installer-relay\sent.txt - ids already handed to Outlook.
  An id is written there right after Outlook accepts it and BEFORE the
  app is told, so a lost "sent" report can never send an email twice
  (the Haber ten-identical-emails lesson: persist first, report second).
#>
param(
  [string]$Base = "https://witty-plant-08257f31e.2.azurestaticapps.net",
  [string]$From = "dinod@ledconnection.com",
  [int]$Every = 15,
  [string]$KeyFile = "",
  [switch]$Once
)
$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Not under AppData: a packaged app (the Claude desktop app) writing there
# lands in a private copy the scheduled task never sees (2026-10-14).
$dir = Join-Path $env:USERPROFILE ".lc-installer-relay"
New-Item -ItemType Directory -Force $dir | Out-Null
$keyFile = if ($KeyFile) { $KeyFile } else { Join-Path $dir "key.txt" }
$logFile = Join-Path $dir "relay.log"
$ledger  = Join-Path $dir "sent.txt"
if (-not (Test-Path $ledger)) { New-Item -ItemType File $ledger | Out-Null }

function Log($m) {
  $line = (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + "  " + $m
  Add-Content -Path $logFile -Value $line -Encoding UTF8
  if ((Get-Item $logFile).Length -gt 2MB) { Move-Item $logFile ($logFile + ".old") -Force }
}

# One relay at a time: two would both send the same message.
$mutex = New-Object System.Threading.Mutex($false, "Local\LCInstallerOutlookRelay")
if (-not $mutex.WaitOne(0)) { Write-Output "Another relay is already running."; exit 0 }

$key = (Get-Content $keyFile -Raw -ErrorAction Stop).Trim()
$hdr = @{ "X-Relay-Key" = $key; "X-LCI" = "1" }

function Ack($id, [bool]$ok, $err) {
  $b = @{ id = $id; ok = $ok }
  if (-not $ok) { $b.error = [string]$err }
  for ($i = 0; $i -lt 3; $i++) {
    try { return Invoke-RestMethod -Method Post -Uri "$Base/api/relay/outbox" -Headers $hdr -ContentType "application/json" -Body ($b | ConvertTo-Json) }
    catch { Start-Sleep -Seconds 2 }
  }
  Log "could not report $id to the app; will report next round"
}

function Get-Account($ol) {
  foreach ($a in $ol.Session.Accounts) { if ($a.SmtpAddress -and $a.SmtpAddress.ToLower() -eq $From.ToLower()) { return $a } }
  return $null
}

function Send-One($ol, $acct, $m) {
  $tmp = Join-Path $env:TEMP ("lci-relay-" + $m.id)
  New-Item -ItemType Directory -Force $tmp | Out-Null
  try {
    $item = $ol.CreateItem(0)
    if ($acct) { $item.SendUsingAccount = $acct }
    $item.To = ($m.to -join "; ")
    if ($m.cc) { $item.CC = ($m.cc -join "; ") }
    if ($m.bcc) { $item.BCC = ($m.bcc -join "; ") }
    $item.Subject = $m.subject
    $item.HTMLBody = $m.html
    foreach ($a in @($m.attachments)) {
      if (-not $a -or -not $a.b64) { continue }
      $safe = ($a.name -replace '[^A-Za-z0-9._-]', '_')
      $p = Join-Path $tmp $safe
      [IO.File]::WriteAllBytes($p, [Convert]::FromBase64String($a.b64))
      $item.Attachments.Add($p) | Out-Null
    }
    $item.Send()
  } finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
  }
}

function Round() {
  $r = Invoke-RestMethod -Method Get -Uri "$Base/api/relay/outbox" -Headers $hdr
  $msgs = @($r.messages)
  if (-not $msgs.Count) { return 0 }
  $done = @{}; Get-Content $ledger | ForEach-Object { if ($_) { $done[$_.Trim()] = $true } }
  $ol = New-Object -ComObject Outlook.Application
  $acct = Get-Account $ol
  if (-not $acct) { Log "no Outlook account for $From; sending from the default account" }
  $n = 0
  foreach ($m in $msgs) {
    if (-not $m -or -not $m.id) { continue }
    if ($done.ContainsKey($m.id)) { Ack $m.id $true $null | Out-Null; continue }   # sent earlier, report was lost
    try {
      Send-One $ol $acct $m
      Add-Content -Path $ledger -Value $m.id -Encoding UTF8                        # persist first
      Ack $m.id $true $null | Out-Null                                             # report second
      Log ("sent " + $m.id + "  to " + ($m.to -join ",") + "  cc " + ($m.cc -join ",") + "  bcc " + ($m.bcc -join ",") + "  " + $m.subject)
      $n++
    } catch {
      Log ("FAILED " + $m.id + ": " + $_.Exception.Message)
      Ack $m.id $false $_.Exception.Message | Out-Null
    }
  }
  # Outlook can hold COM-sent mail in the Outbox until its next sync (seen
  # 2026-10-14, about a minute): push it now.
  if ($n -gt 0) { try { $ol.Session.SendAndReceive($false) } catch { Log ("send/receive: " + $_.Exception.Message) } }
  return $n
}

Log "relay started ($Base, every $Every s)"
do {
  try { $sent = Round; if ($Once) { Write-Output "sent $sent" } }
  catch { Log ("round failed: " + $_.Exception.Message); if ($Once) { Write-Output ("round failed: " + $_.Exception.Message) } }
  if (-not $Once) { Start-Sleep -Seconds $Every }
} while (-not $Once)
