$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Dist = Join-Path $Root "dist"
$Python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $Python) { $Python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $Python) { throw "Python 3 is required to build the DEB and IPK packages." }

& $Python.Source (Join-Path $PSScriptRoot "build-packages.py") --dist $Dist
if ($LASTEXITCODE -ne 0) { throw "Package build failed." }

Write-Host "Architecture-neutral packages created in $Dist"
Write-Host "Install DEB: dpkg -i /tmp/enigma2-plugin-extensions-e2epg_0.5.3_all.deb"
Write-Host "Install IPK: opkg install /tmp/enigma2-plugin-extensions-e2epg_0.5.3_all.ipk"
