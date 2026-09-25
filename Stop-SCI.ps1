$ErrorActionPreference = 'Stop'
$statePath = Join-Path $PSScriptRoot 'logs/processes.json'
if (-not (Test-Path -LiteralPath $statePath)) { throw 'No process state for this app.' }
$sciState = Get-Content -LiteralPath $statePath | ConvertFrom-Json
$all = @(Get-CimInstance Win32_Process)
$targets = @($all | Where-Object {
    ($_.ProcessId -in @($sciState.backend,$sciState.frontend) -or $_.ParentProcessId -eq $sciState.backend) -and
    $_.CommandLine -and $_.CommandLine.Contains($PSScriptRoot) -and
    ($_.CommandLine.Contains('uvicorn backend.main:app') -or $_.CommandLine.Contains('next\dist\bin\next'))
})
foreach ($target in ($targets | Sort-Object ParentProcessId -Descending)) {
    $fresh = Get-CimInstance Win32_Process -Filter "ProcessId=$($target.ProcessId)"
    if ($fresh -and $fresh.CommandLine -eq $target.CommandLine) {
        Stop-Process -Id $target.ProcessId -ErrorAction SilentlyContinue
    }
}
Write-Output 'Stopped only processes recorded for SCI Chatbot.'
