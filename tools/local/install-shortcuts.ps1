param()
$ErrorActionPreference = 'Stop'

$Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$Start = Join-Path $Root 'tools\local\start-local.ps1'
$Stop = Join-Path $Root 'tools\local\stop-local.ps1'
if (-not (Test-Path -LiteralPath $Start)) { throw "Missing $Start" }
if (-not (Test-Path -LiteralPath $Stop)) { throw "Missing $Stop" }

$PowerShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$dash = [char]0x2014
$startName = "AIpedia $dash Local.lnk"
$stopName = "AIpedia $dash Stop Local.lnk"

$desktops = New-Object System.Collections.Generic.List[string]
$desktopDirectory = [Environment]::GetFolderPath('DesktopDirectory')
if (-not $desktopDirectory) { throw 'DesktopDirectory is empty' }
$desktops.Add($desktopDirectory)

$oneDriveDesktop = $null
if ($env:OneDrive) {
    $oneDriveDesktop = Join-Path $env:OneDrive 'Desktop'
    if ((Test-Path -LiteralPath $oneDriveDesktop) -and ($oneDriveDesktop -ne $desktopDirectory)) {
        $desktops.Add($oneDriveDesktop)
    }
}

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class ShortcutNotify {
  [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
  public static extern void SHChangeNotify(int wEventId, uint uFlags, string dwItem1, IntPtr dwItem2);
}
"@

function Write-Shortcut([string]$path, [string]$script, [string]$description) {
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Force
    }
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($path)
    $shortcut.TargetPath = $PowerShell
    $shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$script`""
    $shortcut.WorkingDirectory = $Root
    $shortcut.WindowStyle = 1
    $shortcut.Description = $description
    $shortcut.IconLocation = "$PowerShell,0"
    $shortcut.Save()
    [ShortcutNotify]::SHChangeNotify(0x00000002, 0x0005, $path, [IntPtr]::Zero)
}

$created = @()
foreach ($desktop in $desktops) {
    if (-not (Test-Path -LiteralPath $desktop)) { continue }
    Get-ChildItem -LiteralPath $desktop -Force -Filter 'AIpedia*.lnk' -ErrorAction SilentlyContinue |
        ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }
    $startPath = Join-Path $desktop $startName
    $stopPath = Join-Path $desktop $stopName
    Write-Shortcut $startPath $Start 'Start AIpedia Local on this computer'
    Write-Shortcut $stopPath $Stop 'Stop only AIpedia Local'
    $created += $startPath
    $created += $stopPath
}

[ShortcutNotify]::SHChangeNotify(0x08000000, 0x1000, $null, [IntPtr]::Zero)

$created | ForEach-Object { Write-Output $_ }
