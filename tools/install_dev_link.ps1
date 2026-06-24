$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$AddonSource = Join-Path $RepoRoot "naturetool"
$BlenderAddonRoot = Join-Path $env:APPDATA "Blender Foundation\Blender\4.5\scripts\addons"
$AddonLink = Join-Path $BlenderAddonRoot "naturetool"

if (-not (Test-Path -LiteralPath $AddonSource -PathType Container)) {
    throw "Addon source folder not found: $AddonSource"
}

New-Item -ItemType Directory -Path $BlenderAddonRoot -Force | Out-Null

if (Test-Path -LiteralPath $AddonLink) {
    $item = Get-Item -LiteralPath $AddonLink -Force
    if (-not ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        throw "Target already exists and is not a link: $AddonLink"
    }

    Remove-Item -LiteralPath $AddonLink -Force
}

New-Item -ItemType Junction -Path $AddonLink -Target $AddonSource | Out-Null
Write-Host "Linked $AddonLink -> $AddonSource"
