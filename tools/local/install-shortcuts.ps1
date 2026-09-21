param()
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$Start = Join-Path $Root 'tools\local\start-local.ps1'
$Stop = Join-Path $Root 'tools\local\stop-local.ps1'
$PowerShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$desktops = New-Object System.Collections.Generic.List[string]
$desktops.Add([Environment]::GetFolderPath('Desktop'))
if ($env:OneDrive) {
    $one = Join-Path $env:OneDrive 'Desktop'
    if (Test-Path -LiteralPath $one) { $desktops.Add($one) }
}
$shell = New-Object -ComObject WScript.Shell
$created = @()
foreach ($desktop in $desktops) {
    if (-not $desktop -or -not (Test-Path -LiteralPath $desktop)) { continue }
    $startLnk = $shell.CreateShortcut((Join-Path $desktop 'AIpedia - Local.lnk'))
    $startLnk.TargetPath = $PowerShell
    $startLnk.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$Start`""
    $startLnk.WorkingDirectory = $Root
    $startLnk.WindowStyle = 1
    $startLnk.Description = 'Start AIpedia Local on this computer'
    $startLnk.Save()
    $stopLnk = $shell.CreateShortcut((Join-Path $desktop 'AIpedia - Stop Local.lnk'))
    $stopLnk.TargetPath = $PowerShell
    $stopLnk.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$Stop`""
    $stopLnk.WorkingDirectory = $Root
    $stopLnk.WindowStyle = 1
    $stopLnk.Description = 'Stop only AIpedia Local'
    $stopLnk.Save()
    $created += (Join-Path $desktop 'AIpedia - Local.lnk')
    $created += (Join-Path $desktop 'AIpedia - Stop Local.lnk')
}
# Recreate the Local shortcut with an em dash after COM write, if the filesystem allows it.
foreach ($desktop in $desktops) {
    $ascii = Join-Path $desktop 'AIpedia - Local.lnk'
    $named = Join-Path $desktop ([string]::Concat('AIpedia ', [char]0x2014, ' Local.lnk'))
    $asciiStop = Join-Path $desktop 'AIpedia - Stop Local.lnk'
    $namedStop = Join-Path $desktop ([string]::Concat('AIpedia ', [char]0x2014, ' Stop Local.lnk'))
    if ((Test-Path -LiteralPath $ascii) -and $ascii -ne $named) {
        Move-Item -LiteralPath $ascii -Destination $named -Force
    }
    if ((Test-Path -LiteralPath $asciiStop) -and $asciiStop -ne $namedStop) {
        Move-Item -LiteralPath $asciiStop -Destination $namedStop -Force
    }
}
$created | ForEach-Object { Write-Host $_ }
