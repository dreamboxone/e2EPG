# Packaging targets

The runtime contains only architecture-neutral Python and uses external
`curl`, so the release is published as `Architecture: all` in both DEB and IPK
formats. This covers ARM64 and non-ARM64 Dreamboxes as well as OE-A receivers
such as Vu+ and Gigablue without duplicating identical payloads.

The target files remain as a compatibility inventory for hardware testing.
The package depends on either `python3-sqlite3` or `python-sqlite3`, allowing
modern Python 3 OE-A images and older Python 2 images to resolve their native
SQLite package. Runtime image, Python, Enigma2 API, TLS/CA, and skin behavior
still need representative hardware testing; `all` means CPU-neutral, not that
every vendor-specific skin renderer is automatically supported.
