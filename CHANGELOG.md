# Changelog

## 0.5.3

- Published architecture-neutral `all` packages in both DEB and IPK formats
- Added Python 2/Python 3 SQLite dependency alternatives for DreamOS and OE-A
- Added Enigma2 restart support for systemd, SysV init scripts, and OE-A runlevels
- Added safe package replacement metadata for upgrades from PersianEPG
- Added tagged GitHub Release publishing for both package formats

## 0.5.2

- Removed all compatibility filesystem work from the Enigma2 shutdown path
- Moved skin discovery to a delayed normal-runtime monitor running every ten minutes
- Kept startup lightweight by scheduling the first scan after Enigma2 settles

## 0.5.1

- Anchored translated RTL EPG Next titles immediately after the LTR time column

## 0.5.0

- Added runtime image, architecture, Python, and skin compatibility detection
- Added automatic startup/shutdown scans for newly installed and selected skins
- Added standard and modular skin XML adapters for InfoBar, Channel Selection, and EPG Next
- Added atomic skin writes, original backups, compatibility state, and bounded diagnostics
- Added targeted uninstall cleanup that preserves unrelated skin customizations

## 0.4.2

- Added a dedicated renderer for the Channel Selection EPG Next event list
- Removed the Gemini model identifier from About

## 0.4.1

- Fixed Persian UTF-8 writes to the SQLite cache on DreamOS Python 2
- Added e2EPG converters to Channel Selection event detail widgets
- Removed the debug diagnostics option from the user interface
- Added the plugin version and Telegram support address to setup and About

## 0.4.0

- Renamed the user-facing plugin, runtime directory, converter, data paths, logs, and release artifact to e2EPG
- Replaced the plugin icon with a new e2EPG design
- Changed all plugin UI text to English
- Fixed DreamOS Python 2 crashes by encoding translated Unicode as UTF-8 at the Enigma2/SWIG boundary
- Added migration from PersianEPG while preserving `/root/apikey.txt`, settings, valid Gemini cache, and skin backups

## 0.3.1

- Create the diagnostics log at Enigma2 session startup instead of waiting for setup or the first translated event

## 0.3.0

- Replaced the unfinished native Argos engine with Gemini 3.1 Flash-Lite REST translation
- Added automatic source-language translation to Persian using `/root/apikey.txt`
- Increased cache lifetime to 30 days and added bounded serialization/API cooldown
- Kept API keys out of URLs, process arguments, cache, and logs
- Added rotating component-aware diagnostics for SSH-based development troubleshooting
- Added InfoBar-only skin migration, obsolete-provider cleanup, and automatic Enigma2 restart
- Added disabled packaging profiles for ARMv7, ARM32, MIPS, and MIPSel; release output remains ARM64 DEB only
- Added CI checks for core behavior, Python syntax, maintainer scripts, dependencies, architecture, and stale providers

## 0.2.0

- Added Persian-specific text detection; text containing پ, چ, ژ or گ is never translated
- Added a persisted on/off switch and Persian setup/about screen
- Added 30-day cache expiry, 100MB automatic cache maintenance, and 512KB log rotation
- Added stable CiNo-DreamOSat-Gri-FHD EventName patching during DEB install
- Added component/session-aware rotating diagnostics
- Fixed inverted process-start checks, serialized translation jobs, result refresh, job cleanup, and real timeouts

## 0.1.0

- Initial project skeleton
- Added PersianEPG Enigma2 converter
- Added Google Cloud Translation client using curl
- Added SQLite translation cache
- Added minimal plugin setup screen placeholder
- Added DEB packaging skeleton for Dreambox OS
- Added Plugin Browser icon
- Build Debian package with gzip compression for older Dreambox dpkg compatibility
- Use upload-artifact v7 for Node.js 24 artifact upload
