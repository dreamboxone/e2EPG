# -*- coding: utf-8 -*-
"""Runtime image/skin compatibility and self-healing skin integration."""
import glob
import hashlib
import json
import os
import platform
import re
import tempfile

from .config import CONFIG_DIR, log

STATE_FILE = os.path.join(CONFIG_DIR, "skin-compat.json")
BACKUP_DIR = os.path.join(CONFIG_DIR, "skin-backups")

_SCREEN_RE = re.compile(
    r'(<screen\b[^>]*\bname\s*=\s*(["\'])(?P<name>InfoBar|ChannelSelection)\2[^>]*>)(?P<body>.*?)(</screen\s*>)',
    re.I | re.S)
_EVENT_RE = re.compile(
    r'(<convert\b[^>]*\btype\s*=\s*(["\'])EventName\2[^>]*>\s*)'
    r'(Name|Description|ShortDescription|ExtendedDescription|FullDescription)'
    r'(\s*</convert\s*>)', re.I)
_NEXT_RE = re.compile(r'(\brender\s*=\s*(["\']))EventListDisplay(\2)', re.I)


def _read(path):
    fp = open(path, "rb")
    try:
        return fp.read()
    finally:
        fp.close()


def _unicode(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value


def _bytes(value):
    try:
        unicode_type = unicode
    except NameError:
        unicode_type = str
    return value.encode("utf-8") if isinstance(value, unicode_type) else value


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def detect_platform():
    image = "unknown"
    for path in ("/etc/image-version", "/etc/os-release", "/etc/issue"):
        try:
            text = _unicode(_read(path)[:4096]).replace("\n", " ").strip()
            if text:
                image = "%s:%s" % (path, text[:180])
                break
        except Exception:
            pass
    family = "dreamos" if os.path.exists("/usr/bin/apt-get") else "oe-a" if os.path.exists("/usr/bin/opkg") else "unknown"
    return {
        "family": family,
        "image": image,
        "machine": platform.machine() or "unknown",
        "python": platform.python_version(),
    }


def _skin_files(root="/usr/share/enigma2"):
    paths = set()
    root = os.path.abspath(root)
    base_depth = root.rstrip(os.sep).count(os.sep)
    for directory, subdirs, filenames in os.walk(root):
        subdirs[:] = [name for name in subdirs
                      if os.path.abspath(os.path.join(directory, name)) not in
                      (os.path.abspath(CONFIG_DIR), os.path.abspath(BACKUP_DIR))]
        depth = directory.rstrip(os.sep).count(os.sep) - base_depth
        if depth >= 3:
            subdirs[:] = []
        for filename in filenames:
            if filename.lower().endswith(".xml"):
                paths.add(os.path.join(directory, filename))
    return sorted(path for path in paths if os.path.isfile(path))


def patch_text(text):
    stats = {"infobar": 0, "channel": 0, "next": 0}

    def screen(match):
        name = match.group("name").lower()
        body = match.group("body")

        def event(converter):
            stats["infobar" if name == "infobar" else "channel"] += 1
            return converter.group(1).replace("EventName", "e2EPG") + converter.group(3) + converter.group(4)

        body = _EVENT_RE.sub(event, body)
        if name == "channelselection":
            body, count = _NEXT_RE.subn(r'\1e2EPGEventListDisplay\3', body)
            stats["next"] += count
        return match.group(1) + body + match.group(5)

    return _SCREEN_RE.sub(screen, text), stats


def _load_state():
    try:
        return json.loads(_unicode(_read(STATE_FILE)))
    except Exception:
        return {"files": {}}


def _save_state(state):
    if not os.path.isdir(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    data = json.dumps(state, sort_keys=True, indent=2).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix="e2epg-state-", dir=CONFIG_DIR)
    try:
        os.write(fd, data)
        os.close(fd)
        replace = getattr(os, "replace", os.rename)
        replace(temporary, STATE_FILE)
        os.chmod(STATE_FILE, 0o600)
    except Exception:
        try:
            os.close(fd)
        except Exception:
            pass
        try:
            os.unlink(temporary)
        except Exception:
            pass
        raise


def _write_atomic(path, data, mode):
    directory = os.path.dirname(path)
    fd, temporary = tempfile.mkstemp(prefix=".e2epg-", dir=directory)
    try:
        os.write(fd, data)
        os.close(fd)
        os.chmod(temporary, mode)
        replace = getattr(os, "replace", os.rename)
        replace(temporary, path)
    except Exception:
        try:
            os.close(fd)
        except Exception:
            pass
        try:
            os.unlink(temporary)
        except Exception:
            pass
        raise


def scan_and_patch(root="/usr/share/enigma2"):
    platform_info = detect_platform()
    state = _load_state()
    state["platform"] = platform_info
    files = state.setdefault("files", {})
    totals = {"scanned": 0, "changed": 0, "infobar": 0, "channel": 0, "next": 0, "unsupported": 0}
    if not os.path.isdir(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        os.chmod(BACKUP_DIR, 0o700)

    for path in _skin_files(root):
        totals["scanned"] += 1
        try:
            raw = _read(path)
            text = _unicode(raw)
            patched_text, stats = patch_text(text)
            patched = _bytes(patched_text)
            for key in ("infobar", "channel", "next"):
                totals[key] += stats[key]
            if patched == raw:
                if ("<screen" in text and ("InfoBar" in text or "ChannelSelection" in text) and
                        "e2EPG" not in text and "EventName" not in text and "EventListDisplay" not in text):
                    totals["unsupported"] += 1
                continue

            original_hash = _sha(raw)
            record = files.get(path, {})
            if not record.get("backup"):
                backup = os.path.join(BACKUP_DIR, hashlib.sha1(path.encode("utf-8")).hexdigest() + ".xml")
                if not os.path.exists(backup):
                    _write_atomic(backup, raw, 0o600)
                record["backup"] = backup
                record["original_sha256"] = original_hash
            mode = os.stat(path).st_mode & 0o777
            _write_atomic(path, patched, mode)
            record["patched_sha256"] = _sha(patched)
            record["stats"] = stats
            files[path] = record
            totals["changed"] += 1
            log("compat patched skin=%s stats=%s" % (path, stats), component="compat")
        except Exception as exc:
            totals["unsupported"] += 1
            log("compat skin failed path=%s error=%s" % (path, exc), "ERROR", "compat", True)

    _save_state(state)
    log("compat scan family=%s machine=%s python=%s results=%s" %
        (platform_info["family"], platform_info["machine"], platform_info["python"], totals),
        component="compat")
    return totals
