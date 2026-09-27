param()
$ErrorActionPreference = 'Stop'

$Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$Context = Join-Path $Root 'AI_CONTEXT'
$HistoryHtml = Join-Path $Root 'timeline.html'
$ShortcutPath = Join-Path $Context 'AIpedia — История сайта.lnk'

if (-not (Test-Path -LiteralPath $Context)) { throw "Missing $Context" }
if (-not (Test-Path -LiteralPath $HistoryHtml)) {
    throw "Missing $HistoryHtml. Rebuild it with tools/pack_ai_context.py first."
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = $HistoryHtml
$shortcut.Arguments = ''
$shortcut.WorkingDirectory = $Root
$shortcut.WindowStyle = 7
$shortcut.Description = 'Open the standalone AIpediya site history'
$shortcut.IconLocation = "$HistoryHtml,0"
$shortcut.Save()

Write-Output $ShortcutPath
