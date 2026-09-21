param([int]$Port = 0)
$ErrorActionPreference = 'Stop'
$starter = Join-Path $PSScriptRoot 'tools\local\start-local.ps1'
if ($Port -gt 0) { $env:AIPEDIA_LOCAL_PORT = [string]$Port }
& $starter
if ($LASTEXITCODE -ne 0) { throw 'AIpedia Local did not start.' }
