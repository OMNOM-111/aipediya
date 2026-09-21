param()
$ErrorActionPreference = 'Stop'
try { $Host.UI.RawUI.WindowTitle = 'AIpedia - Local' } catch {}

$Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
Set-Location -LiteralPath $Root
$LocalDir = Join-Path $Root 'data\local'
$LogDir = Join-Path $Root 'logs'
$LogFile = Join-Path $LogDir 'local-launcher.log'
$PidFile = Join-Path $LocalDir 'aipedia.pid'
$PortFile = Join-Path $LocalDir 'port.txt'
$DbFile = Join-Path $LocalDir 'aipedia.sqlite3'
$SecretFile = Join-Path $LocalDir 'secret.key'
$Python = Join-Path $Root '.venv\Scripts\python.exe'
$LockFile = Join-Path $Root 'requirements.lock'
$PreferredPort = 18810
if ($env:AIPEDIA_LOCAL_PORT -match '^\d+$') { $PreferredPort = [int]$env:AIPEDIA_LOCAL_PORT}

New-Item -ItemType Directory -Force -Path $LocalDir, $LogDir | Out-Null

function Write-Log([string]$Message) {
    $line = '{0:o} {1}' -f [DateTime]::UtcNow, $Message
    Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
    Write-Host $Message
}

function Show-Failure([string]$Message) {
    Write-Log $Message
    Write-Host ""
    Write-Host "Local did not start. No other process was stopped."
    Write-Host "Log: $LogFile"
    if ([Environment]::UserInteractive) { Read-Host 'Press Enter to close' | Out-Null }
    exit 1
}

function Get-PortOwner([int]$Port) {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Where-Object { $_.LocalAddress -in @('127.0.0.1', '::1', '::ffff:127.0.0.1') } |
        Select-Object -First 1
}

function Get-ProcessCommand([int]$ProcessId) {
    try { return [string](Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId").CommandLine }
    catch { return '' }
}

function Read-Health([int]$Port) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/healthz" -UseBasicParsing -TimeoutSec 2
        return $response.Content | ConvertFrom-Json
    } catch { return $null }
}

function Test-OurLocal([int]$Port) {
    $health = Read-Health $Port
    return [bool]($health -and $health.service -eq 'aipedia' -and $health.environment -eq 'local')
}

function Choose-Port {
    for ($p = 18810; $p -le 18819; $p++) {
        if (Test-OurLocal $p) { return @{ Port = $p; Existing = $true } }
    }
    $candidates = @($PreferredPort)
    if (Test-Path -LiteralPath $PortFile) {
        $raw = (Get-Content -LiteralPath $PortFile -Raw).Trim()
        if ($raw -match '^\d+$') { $candidates = @([int]$raw) + $candidates }
    }
    for ($p = 18810; $p -le 18819; $p++) { $candidates += $p }
    $seen = @{}
    foreach ($port in $candidates) {
        if ($port -lt 18810 -or $port -gt 18819) { continue }
        if ($seen.ContainsKey($port)) { continue }
        $seen[$port] = $true
        if (Test-OurLocal $port) { return @{ Port = $port; Existing = $true } }
        $owner = Get-PortOwner $port
        if (-not $owner) { return @{ Port = $port; Existing = $false } }
        Write-Log "Port $port is in use by PID $($owner.OwningProcess). That process will not be stopped."
    }
    throw "No free loopback port from 18810 to 18819"
}

try {
    Write-Log "Project: $Root"
    if (-not (Test-Path -LiteralPath $Python)) {
        Write-Log 'Creating .venv from pinned requirements.lock'
        $created = $false
        if (Get-Command py -ErrorAction SilentlyContinue) {
            & py -3.12 -m venv (Join-Path $Root '.venv')
            if ($LASTEXITCODE -eq 0) { $created = $true }
        }
        if (-not $created) {
            & python -m venv (Join-Path $Root '.venv')
        }
        if (-not (Test-Path -LiteralPath $Python)) { throw 'Could not create .venv with Python 3.12+' }
        & $Python -m pip install -r $LockFile
        if ($LASTEXITCODE -ne 0) { throw 'pip install -r requirements.lock failed' }
    }
    & $Python -c "import django, waitress"
    if ($LASTEXITCODE -ne 0) {
        Write-Log 'Installing pinned dependencies into .venv'
        & $Python -m pip install -r $LockFile
        if ($LASTEXITCODE -ne 0) { throw 'pip install -r requirements.lock failed' }
    }

    if (-not (Test-Path -LiteralPath $SecretFile)) {
        $secret = & $Python -c "import secrets; print(secrets.token_urlsafe(64))"
        Set-Content -LiteralPath $SecretFile -Value $secret.Trim() -Encoding ASCII
    }

    $env:AIPEDIA_ENV = 'local'
    $env:AIPEDIA_DB = $DbFile
    $env:AIPEDIA_SECRET_KEY = (Get-Content -LiteralPath $SecretFile -Raw).Trim()
    $env:AIPEDIA_ALLOWED_HOSTS = '127.0.0.1,localhost,[::1]'
    $env:AIPEDIA_PUBLIC_ORIGIN = 'https://aipediya.com'
    $env:AIPEDIA_PID_FILE = $PidFile
    Remove-Item Env:AIPEDIA_TRUST_PROXY -ErrorAction SilentlyContinue
    Remove-Item Env:AIPEDIA_INDEXNOW_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:AIPEDIA_ADS_ENABLED -ErrorAction SilentlyContinue

    Write-Log 'Preparing Local catalog if needed (existing database is kept)'
    & $Python (Join-Path $PSScriptRoot 'prepare_local_catalog.py')
    if ($LASTEXITCODE -ne 0) { throw 'Could not prepare the Local catalog snapshot' }

    & $Python (Join-Path $Root 'manage.py') migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw 'Local migrate failed' }
    & $Python (Join-Path $Root 'manage.py') check
    if ($LASTEXITCODE -ne 0) { throw 'Local django check failed' }

    $choice = Choose-Port
    $port = [int]$choice.Port
    Set-Content -LiteralPath $PortFile -Value "$port" -Encoding ASCII
    $url = "http://127.0.0.1:$port/?lang=ru"

    if ($choice.Existing) {
        Write-Log "Local is already running at $url"
        Start-Process $url
        Write-Host "Opened the existing Local catalog. Closing the browser does not stop the server."
        Write-Host "Stop Local: $Root\tools\local\stop-local.ps1"
        exit 0
    }

    Write-Log "Starting Local Waitress on 127.0.0.1:$port"
    $serve = Join-Path $Root 'tools\serve.py'
    $proc = Start-Process -FilePath $Python -ArgumentList @($serve, '--port', "$port") -WorkingDirectory $Root -NoNewWindow -PassThru
    $ready = $false
    for ($i = 0; $i -lt 45; $i++) {
        if ($proc.HasExited) { throw "Local server exited with code $($proc.ExitCode)" }
        if (Test-OurLocal $port) { $ready = $true; break }
        Start-Sleep -Seconds 1
    }
    if (-not $ready) { throw "Local did not become ready on $url" }
    Start-Process $url
    Write-Host ""
    Write-Host "AIpedia Local is ready: $url"
    Write-Host "Database: $DbFile"
    Write-Host "Stop: close this window, press Ctrl+C, or run tools\local\stop-local.ps1"
    Write-Host "Closing the browser does not stop Local."
    Wait-Process -Id $proc.Id
} catch {
    Show-Failure $_.Exception.Message
}
