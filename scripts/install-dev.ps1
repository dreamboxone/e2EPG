param(
    [string]$HostName = "dreambox",
    [string]$User = "root",
    [string]$Package = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

if (-not $Package) {
    $Package = Join-Path $Root "dist\enigma2-plugin-extensions-e2epg_0.5.3_all.deb"
}
if (-not (Test-Path -LiteralPath $Package -PathType Leaf)) {
    throw "Enigma2 package not found: $Package"
}

# Install the package instead of copying Python files directly. This guarantees
# that cleanup, InfoBar migration, dependency checks, and restart all run.
$Extension = [System.IO.Path]::GetExtension($Package).ToLowerInvariant()
if ($Extension -notin @(".deb", ".ipk")) {
    throw "Only .deb and .ipk packages are supported: $Package"
}
$RemotePackage = "/tmp/$([System.IO.Path]::GetFileName($Package))"
scp -- "$Package" "${User}@${HostName}:$RemotePackage"
if ($Extension -eq ".ipk") {
    ssh "${User}@${HostName}" "opkg install '$RemotePackage'"
} else {
    ssh "${User}@${HostName}" "dpkg -i '$RemotePackage'"
}
