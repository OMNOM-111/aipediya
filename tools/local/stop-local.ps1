param()
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$PidFile = Join-Path $Root 'data\local\aipedia.pid'
$PortFile = Join-Path $Root 'data\local\port.txt'

function Get-ProcessCommand([int]$ProcessId) {
    try { return [string](Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId").CommandLine }
    catch { return '' }
}

if (-not (Test-Path -LiteralPath $PidFile)) {
    Write-Host 'AIpedia Local is not running (no pid file).'
    exit 0
}
$raw = (Get-Content -LiteralPath $PidFile -Raw).Trim()
$ProcessId = 0
if (-not [int]::TryParse($raw, [ref]$ProcessId) -or $ProcessId -le 0) {
    Write-Host 'Pid file is invalid; leaving other processes untouched.'
    exit 1
}
$proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
if (-not $proc) {
    Remove-Item -LiteralPath $PidFile -ErrorAction SilentlyContinue
    Write-Host 'AIpedia Local was not running. Removed a stale pid file.'
    exit 0
}
$cmd = Get-ProcessCommand $ProcessId
$rootPattern = [regex]::Escape($Root)
$isServe = $cmd -match 'serve\.py'
$inProject = ($cmd -match $rootPattern) -or ($proc.Path -like "$Root*")
if (-not $isServe -or -not $inProject) {
    Write-Host "PID $ProcessId is not this project's Local server. It was not stopped."
    exit 1
}
Stop-Process -Id $ProcessId
$left = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
if ($left) {
    Write-Host "PID $ProcessId did not exit. It was not force-killed."
    exit 1
}
Remove-Item -LiteralPath $PidFile -ErrorAction SilentlyContinue
$port = ''
if (Test-Path -LiteralPath $PortFile) { $port = (Get-Content -LiteralPath $PortFile -Raw).Trim() }
Write-Host "Stopped AIpedia Local only$(if ($port) { " (was 127.0.0.1:$port)" })."
Write-Host 'Production, tunnels and other programs were not changed.'
