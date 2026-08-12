# -*- coding: utf-8 -*-
"""Small, dependency-free logger for DreamOS/Python 2.7."""
import os
import sys
import time
import traceback


LOG_FILE = "/tmp/e2EPG.log"
LOG_BACKUP_FILE = LOG_FILE + ".1"
LOG_MAX_BYTES = 512 * 1024
SESSION_ID = "%08x" % (int(time.time() * 1000) & 0xffffffff)


def _text(value):
    try:
        text_type = unicode
        byte_type = str
    except NameError:
        text_type = str
        byte_type = bytes
    if isinstance(value, text_type):
        return value
    if isinstance(value, byte_type):
        return value.decode("utf-8", "replace")
    try:
        return text_type(value)
    except Exception:
        return u"<unprintable>"


def _debug_enabled():
    # Development diagnostics are always collected. There is deliberately no
    # user-facing switch; the bounded rotating log prevents unbounded growth.
    return True


def log(message, level="INFO", component="core", exc_info=False):
    """Write one bounded UTF-8 record. Logging must never break Enigma2."""
    level = (level or "INFO").upper()
    if level == "DEBUG" and not _debug_enabled():
        return
    try:
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) >= LOG_MAX_BYTES:
            try:
                if os.path.exists(LOG_BACKUP_FILE):
                    os.unlink(LOG_BACKUP_FILE)
                os.rename(LOG_FILE, LOG_BACKUP_FILE)
            except Exception:
                pass
        detail = _text(message).replace(u"\r", u"\\r").replace(u"\n", u"\\n")
        if exc_info:
            detail += u" | " + _text(traceback.format_exc()).replace(u"\r", u"").replace(u"\n", u" | ")
        line = u"%s %-7s session=%s component=%s %s\n" % (
            time.strftime("%Y-%m-%d %H:%M:%S"), level, SESSION_ID, component, detail
        )
        fp = open(LOG_FILE, "ab")
        try:
            fp.write(line.encode("utf-8", "replace"))
        finally:
            fp.close()
    except Exception:
        pass


def runtime_summary():
    try:
        from .config import API_KEY_FILE, get_cache_path, read_api_key
        api_key = "yes" if read_api_key() else "no"
        key_mode = oct(os.stat(API_KEY_FILE).st_mode & 0o777) if os.path.isfile(API_KEY_FILE) else "missing"
        cache_path = get_cache_path()
        cache_size = os.path.getsize(cache_path) if os.path.exists(cache_path) else 0
        return ("python=%s.%s.%s api_key=%s key_mode=%s cache_bytes=%s cache=%s" %
                (sys.version_info[0], sys.version_info[1], sys.version_info[2], api_key,
                 key_mode, cache_size, cache_path))
    except Exception:
        return "runtime summary unavailable"
