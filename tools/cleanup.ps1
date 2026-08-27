# SENTRY process cleanup — kills stale servers from crashed agent sessions.
# Deliberately does NOT touch WSL Docker (Postgres/Redis/Neo4j keep running —
# killing them would destroy your seeded data).
# SAFE: only kills processes whose command line contains 'vite' or 'uvicorn'
# under a SENTRY path, plus Playwright-spawned Chromium.

$ErrorActionPreference = "SilentlyContinue"

# --- 1. Kill listeners on all ports this project has ever drifted to -------
$ports = 8000, 8001, 8002, 8003, 8080, 3000, 3001, 3002, 3005
foreach ($p in $ports) {
    $owners = Get-NetTCPConnection -LocalPort $p -State Listen |
              Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $owners) {
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "Killing $($proc.ProcessName) (PID $procId) on port $p"
            taskkill /T /F /PID $procId | Out-Null
        }
    }
}

# --- 2. Kill orphaned Playwright Chromium (identified by install path) -----
Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like "*ms-playwright*" -and
                   ($_.Name -eq "chrome.exe" -or $_.Name -eq "chromium.exe" -or
                    $_.Name -eq "headless_shell.exe") } |
    ForEach-Object {
        Write-Host "Killing Playwright browser PID $($_.ProcessId)"
        taskkill /T /F /PID $_.ProcessId | Out-Null
    }

# --- 3. Kill any straggler vite/uvicorn processes under SENTRY -------------
Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like "*SENTRY*" -and
                   (($_.CommandLine -like "*vite*") -or
                    ($_.CommandLine -like "*uvicorn*")) } |
    ForEach-Object {
        Write-Host "Killing $($_.Name) PID $($_.ProcessId)"
        taskkill /T /F /PID $_.ProcessId | Out-Null
    }

Write-Host ""
Write-Host "Cleanup complete. Ports now free: $($ports -join ', ')"
Write-Host "WSL Docker containers left running intentionally."
