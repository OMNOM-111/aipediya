param(
    [ValidateSet('/ru/', '/ru/history/')]
    [string]$OpenPath = '/ru/'
)
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
# One canonical Local: this repository, its data\local SQLite, 127.0.0.1:18810.
# AIPEDIA_LOCAL_PORT is only for an explicit temporary QA run (18810-18819);
# the launcher never adopts or falls back to another port or worktree.
$CanonicalPort = 18810
$Port = $CanonicalPort
if ($env:AIPEDIA_LOCAL_PORT -match '^\d+$') { $Port = [int]$env:AIPEDIA_LOCAL_PORT }

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

function Test-AIpediaLocal([int]$Port) {
    $health = Read-Health $Port
    return [bool]($health -and $health.service -eq 'aipedia' -and $health.environment -eq 'local')
}

function Get-ServeCommands([int]$ProcessId) {
    # The listener may be the base interpreter started by the .venv shim, so
    # check the process and its parent.
    $commands = @()
    try {
        $p = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId"
        if ($p) {
            $commands += [string]$p.CommandLine
            $parent = Get-CimInstance Win32_Process -Filter "ProcessId=$($p.ParentProcessId)" -ErrorAction SilentlyContinue
            if ($parent) { $commands += [string]$parent.CommandLine }
        }
    } catch {}
    return $commands
}

function Test-ThisProjectLocal([int]$Port) {
    # Ours only when /healthz is an AIpedia Local AND the listening process runs
    # this repository's tools\serve.py; a Local of another worktree is not ours.
    if (-not (Test-AIpediaLocal $Port)) { return $false }
    $owner = Get-PortOwner $Port
    if (-not $owner) { return $false }
    $serve = [regex]::Escape((Join-Path $Root 'tools\serve.py'))
    foreach ($cmd in (Get-ServeCommands ([int]$owner.OwningProcess))) {
        if ($cmd -match $serve) { return $true }
    }
    return $false
}

function Choose-Port {
    if ($Port -lt 18810 -or $Port -gt 18819) { throw "Local port must be 18810-18819 (got $Port)" }
    for ($p = 18810; $p -le 18819; $p++) {
        if ($p -ne $Port -and (Test-AIpediaLocal $p) -and -not (Test-ThisProjectLocal $p)) {
            Write-Log "Note: another AIpedia Local (other worktree or temporary QA) answers on port $p. It is not this Local and was not used or stopped."
        }
    }
    if (Test-ThisProjectLocal $Port) { return @{ Port = $Port; Existing = $true } }
    $owner = Get-PortOwner $Port
    if ($owner) {
        $cmd = (Get-ServeCommands ([int]$owner.OwningProcess)) -join ' <- '
        throw "Port $Port is used by PID $($owner.OwningProcess) ($cmd), which is not this repository's Local. It was not stopped; free the port and run the shortcut again."
    }
    return @{ Port = $Port; Existing = $false }
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
    $url = "http://127.0.0.1:$port$OpenPath"

    if ($choice.Existing) {
        Write-Log "Local is already running at $url"
        try { Start-Process $url } catch { Write-Log "Local is ready; open manually: $url" }
        Write-Host "Existing Local is ready. Closing the browser does not stop the server."
        Write-Host "Stop Local: $Root\tools\local\stop-local.ps1"
        exit 0
    }

    Write-Log "Starting Local Waitress on 127.0.0.1:$port"
    $serve = Join-Path $Root 'tools\serve.py'
    $proc = Start-Process -FilePath $Python -ArgumentList @($serve, '--port', "$port") -WorkingDirectory $Root -WindowStyle Hidden -PassThru
    $ready = $false
    for ($i = 0; $i -lt 45; $i++) {
        if ($proc.HasExited) { throw "Local server exited with code $($proc.ExitCode)" }
        if (Test-ThisProjectLocal $port) { $ready = $true; break }
        Start-Sleep -Seconds 1
    }
    if (-not $ready) { throw "Local did not become ready on $url" }
    try { Start-Process $url } catch { Write-Log "Local is ready; open manually: $url" }
    Write-Host ""
    Write-Host "AIpedia Local is ready: $url"
    Write-Host "Database: $DbFile"
    Write-Host "Stop: close this window, press Ctrl+C, or run tools\local\stop-local.ps1"
    Write-Host "Closing the browser does not stop Local."
    Wait-Process -Id $proc.Id
} catch {
    Show-Failure $_.Exception.Message
}
