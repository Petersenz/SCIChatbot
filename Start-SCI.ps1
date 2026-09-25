$ErrorActionPreference = 'Stop'
$appRoot = $PSScriptRoot
$logRoot = Join-Path $appRoot 'logs'
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
foreach ($port in @(8010,3100)) {
    $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        try {
            $probe = Invoke-RestMethod 'http://127.0.0.1:3100/api/health' -TimeoutSec 5
            if ($probe.application -eq 'sci-chatbot-capstone') {
                Write-Output 'SCI Chatbot is already running: http://127.0.0.1:3100'
                exit 0
            }
        } catch {}
        throw "Port $port is in use. No existing process was stopped."
    }
}
$pythonPath = Join-Path $appRoot '.venv/Scripts/python.exe'
$nodePath = (Get-Command node).Source
$nextPath = Join-Path $appRoot 'frontend/node_modules/next/dist/bin/next'
$lanAddresses = @(Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway } | ForEach-Object { $_.IPv4Address.IPAddress })
$env:SCI_ALLOWED_ORIGINS = ($lanAddresses | ForEach-Object { "http://${_}:3100" }) -join ','
$backend = Start-Process -FilePath $pythonPath -ArgumentList @('-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8010') -WorkingDirectory $appRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logRoot 'backend.log') -RedirectStandardError (Join-Path $logRoot 'backend-error.log') -PassThru
@{backend=$backend.Id;frontend=0;started=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $logRoot 'processes.json')
$ready = $false
for ($attempt = 0; $attempt -lt 360; $attempt++) {
    try {
        $probe = Invoke-RestMethod 'http://127.0.0.1:8010/api/health' -TimeoutSec 2
        if ($probe.application -eq 'sci-chatbot-capstone') { $ready = $true; break }
    } catch {}
    Start-Sleep -Milliseconds 500
}
if (-not $ready) { throw 'SCI Chatbot did not become ready. See logs/backend-error.log and logs/frontend-error.log.' }
$frontend = Start-Process -FilePath $nodePath -ArgumentList @(('"'+$nextPath+'"'),'start','--hostname','0.0.0.0','--port','3100') -WorkingDirectory (Join-Path $appRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logRoot 'frontend.log') -RedirectStandardError (Join-Path $logRoot 'frontend-error.log') -PassThru
@{backend=$backend.Id;frontend=$frontend.Id;started=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $logRoot 'processes.json')
$webReady = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        $probe = Invoke-RestMethod 'http://127.0.0.1:3100/api/health' -TimeoutSec 2
        if ($probe.application -eq 'sci-chatbot-capstone') { $webReady = $true; break }
    } catch {}
    Start-Sleep -Milliseconds 500
}
if (-not $webReady) { throw 'Frontend did not become ready. See logs/frontend-error.log.' }
Write-Output 'SCI Chatbot: http://127.0.0.1:3100'
foreach ($lanAddress in $lanAddresses) { Write-Output "SCI Chatbot (LAN): http://${lanAddress}:3100" }
Write-Output 'Login accounts: data/local-accounts.json'
