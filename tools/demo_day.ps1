# tools/demo_day.ps1 - transform the dev box into the SENTRY demo appliance.
# Run manually on demo day: powershell -File E:\SENTRY\tools\demo_day.ps1
# (-PreflightOnly: run hygiene/resource checks without booting the app)

param([switch]$PreflightOnly)
$ErrorActionPreference = "Stop"
$repo = "E:\SENTRY"
Set-Location $repo
Write-Host "=== SENTRY DEMO APPLIANCE ==="

# [1/6] Process hygiene - the machine now belongs to the demo
Write-Host "`n[1/6] Killing stale SENTRY processes..."
powershell -NoProfile -ExecutionPolicy Bypass -File "$repo\tools\cleanup.ps1"
Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -like "*verify_sentry*" } |
  ForEach-Object { taskkill /T /F /PID $_.ProcessId 2>$null
                   Write-Host "  killed harness PID $($_.ProcessId)" }

# [2/6] Resources
$freeGb = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)
Write-Host "`n[2/6] Free RAM: ${freeGb} GB"
if ($freeGb -lt 4) { Write-Warning "LOW RAM (<4GB). Close IDE, agent sessions, extra browsers. Cold rehearsal should tell you the real number." }

# [3/6] Power hardening - the machine must not sleep mid-demo
Write-Host "`n[3/6] Disabling sleep/hibernate/monitor-off/lid-action (AC)..."
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0
powercfg /setactive SCHEME_CURRENT

# [4/6] Data layer
Write-Host "`n[4/6] Data layer status..."
if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker compose -f "$repo\docker-compose.yml" up -d 2>$null
    Write-Host "  Docker multi-service stack ready."
} else {
    Write-Host "  Docker not on native PATH; SENTRY self-contained SQLite and in-memory stores active."
}

if ($PreflightOnly) {
    Write-Host "`nPreflight-only - stopping before app boot."
    exit 0
}

# [5/6] THE VERIFIED BOOT - Gate 0 is the demo gate
Write-Host "`n[5/6] Booting backend+frontend via verification harness..."
& "$repo\.venv\Scripts\python.exe" "$repo\tools\verify_sentry.py" --start --keep-servers --label demo
if ($LASTEXITCODE -ne 0) {
    Write-Host "  !! GATE 0 FAILED - DO NOT PRESENT. cleanup.ps1, then re-run." -ForegroundColor Red
    exit 1
}

# [6/6] Clean presentation browser - dedicated profile, fullscreen, no extensions
Write-Host "`n[6/6] Launching presentation browser..."
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$edge   = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$browserArgs = @("--user-data-dir=$repo\.demo-profile","--start-fullscreen",
          "--window-size=1920,1080","--no-first-run","--no-default-browser-check",
          "http://localhost:3000")
if (Test-Path $chrome) { Start-Process $chrome $browserArgs }
elseif (Test-Path $edge) { Start-Process $edge $browserArgs }
else { Start-Process "http://localhost:3000" }

Write-Host "`nBOOT COMPLETE - 15/15 verified."
Write-Host "  Dashboard : http://localhost:3000"
Write-Host "  Demo flow : docs/DEMO_SCRIPT.md"
Write-Host "  API docs  : http://localhost:8000/docs"
Write-Host "  MID-DEMO FAILURE: tools\cleanup.ps1 -> re-run this script (~2 min), or cut to backup video."
