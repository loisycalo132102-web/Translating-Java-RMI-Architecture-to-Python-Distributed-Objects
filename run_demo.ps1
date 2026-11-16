# Launches Terminal 1 (Server) and Terminal 2 (Client) in separate PowerShell windows
Write-Host "Starting Python RMI Distributed Lab Demonstration..." -ForegroundColor Cyan

$baseDir = $PSScriptRoot
if (-not $baseDir) { $baseDir = Get-Location }

# Start Server
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$baseDir'; Write-Host 'Terminal 1: Server Daemon' -ForegroundColor Cyan; python PYTHON_RMI_LAB/server.py"

Start-Sleep -Seconds 2

# Start Client
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$baseDir'; Write-Host 'Terminal 2: Distributed Client' -ForegroundColor Cyan; python PYTHON_RMI_LAB/client.py; Write-Host '`n--- Querying single item: laptop ---' -ForegroundColor Yellow; python PYTHON_RMI_LAB/client.py --item laptop"

Write-Host "Both terminals launched on your desktop!" -ForegroundColor Green
