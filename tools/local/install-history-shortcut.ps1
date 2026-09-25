param()
$ErrorActionPreference = 'Stop'

$Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$Context = Join-Path $Root 'AI_CONTEXT'
$Launcher = Join-Path $Root 'tools\local\start-local.ps1'
$ShortcutPath = Join-Path $Context 'AIpedia — История сайта.lnk'
$PowerShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'

if (-not (Test-Path -LiteralPath $Launcher)) { throw "Missing $Launcher" }
if (-not (Test-Path -LiteralPath $Context)) { throw "Missing $Context" }
if (-not (Test-Path -LiteralPath $PowerShell)) { throw "Missing $PowerShell" }

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = $PowerShell
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$Launcher`" -OpenPath `"/ru/history/`""
$shortcut.WorkingDirectory = $Root
$shortcut.WindowStyle = 1
$shortcut.Description = 'Start or open AIpedia Local product history'
$shortcut.IconLocation = "$PowerShell,0"
$shortcut.Save()

Write-Output $ShortcutPath
