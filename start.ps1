param([int]$Port = 18810)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$AipediaPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $AipediaPython)) { throw 'Create .venv and install requirements.lock first; see README.md.' }
& $AipediaPython tools/serve.py --port $Port
if ($LASTEXITCODE -ne 0) { throw 'AIpedia did not start. The port may already be in use.' }
