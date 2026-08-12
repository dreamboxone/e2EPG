# e2EPG

e2EPG is an Enigma2 plugin/converter that translates satellite EPG text
from any language to Persian using the Gemini API.

Supported package families:

- DreamOS Dreamboxes on ARM64 and non-ARM64 CPUs
- OE-A receivers, including Vu+ and Gigablue
- Enigma2 with Python 2.7 or Python 3
- `curl` with HTTPS and a valid CA certificate store

## How it works

The plugin translates event titles, short descriptions, and extended
descriptions when they are displayed. It does not modify Enigma2's EPG
database. The original text remains visible while a translation is pending or
if a request fails.

Translations use `gemini-3.1-flash-lite` and are cached in SQLite for 30 days.
Requests are serialized, the queue is bounded, and API failures activate a
cooldown to protect the API quota and receiver.

EPG text is sent to Google's Gemini service for translation. Users should take
this privacy implication into account before enabling the plugin.

## API key

Create this file on the receiver:

```text
/root/apikey.txt
```

The file must contain only the Gemini API key on one line. Recommended
permissions:

```sh
chmod 600 /root/apikey.txt
```

The key is never included in a command line, URL, SQLite cache, or diagnostic
log. A temporary curl configuration with mode `0600` is removed after every
request.

## Skin usage

Replace a standard converter such as:

```xml
<convert type="EventName">Name</convert>
```

with:

```xml
<convert type="e2EPG">Name</convert>
```

Supported modes are `Name`, `ShortDescription`, `ExtendedDescription`, and
`FullDescription`.

The compatibility layer detects DreamOS/OE-A, CPU architecture, Python version,
and standard or modular skin XML. A delayed normal-runtime monitor scans every
ten minutes, so skins installed or selected after e2EPG are integrated for the
next Enigma2 start without filesystem work during shutdown. Standard InfoBar,
Channel Selection, native ServiceList,
and EventListDisplay EPG Next paths are supported. Unknown proprietary
renderers are left untouched and reported in `/tmp/e2EPG.log`.

Skin writes are atomic. Original files and compatibility state are kept under
`/etc/enigma2/e2EPG/skin-backups` and `/etc/enigma2/e2EPG/skin-compat.json`.
Uninstall reverses only e2EPG converter/renderer markers.

The release provides architecture-neutral `all` packages in DEB and IPK
formats. The payload is pure Python and supports ARM64, ARMv7/armhf, 32-bit
ARM/armel, MIPS, and MIPSel. The package dependency accepts either
`python3-sqlite3` or `python-sqlite3`, covering modern Python 3 OE-A images and
older Python 2 images. Vendor-specific skin renderers may still require an
adapter even though the plugin itself is CPU-neutral.

## Diagnostics

Enable **Debug diagnostics** in setup when troubleshooting a development build.
Logs are intentionally not displayed in the plugin UI. Files are bounded and rotated:

```text
/tmp/e2EPG.log
/tmp/e2EPG.log.1
```

EPG text and the API key are not logged. View the log over SSH:

```sh
tail -f /tmp/e2EPG.log
```

## Build and install

Build both packages on Windows, Linux, or macOS with Python 3:

```powershell
.\scripts\build-deb.ps1
```

Or invoke the cross-platform builder directly:

```sh
python3 scripts/build-packages.py
```

Install the matching format (Enigma2 restarts automatically):

```sh
dpkg -i /tmp/enigma2-plugin-extensions-e2epg_0.5.3_all.deb
opkg install /tmp/enigma2-plugin-extensions-e2epg_0.5.3_all.ipk
```

The package automatically restarts Enigma2 after a successful install or
removal. Upgrading removes obsolete Google/Argos files, models, old-provider
cache, and old logs. `/root/apikey.txt` is always preserved, including purge.
