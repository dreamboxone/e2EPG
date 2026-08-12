# -*- coding: utf-8 -*-
import hashlib
import os
import sqlite3
import time

from .config import CACHE_MAX_BYTES, CACHE_TTL_SECONDS, get_cache_path, log

try:
    text_type = unicode
except NameError:
    text_type = str


class TranslationCache(object):
    def __init__(self):
        self.path = get_cache_path()
        try:
            self._init_db()
            log("cache ready path=%s" % self.path, component="cache")
        except Exception:
            log("cache initialization failed path=%s" % self.path, "ERROR", "cache", True)
            raise

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=3)
        # DreamOS still uses Python 2.  sqlite must receive unicode for TEXT
        # columns; UTF-8 byte strings containing Persian otherwise raise
        # ProgrammingError and the successful translation is lost.
        db.text_factory = text_type
        return db

    def _text(self, value):
        if value is None or isinstance(value, text_type):
            return value
        try:
            return value.decode("utf-8")
        except (AttributeError, UnicodeDecodeError):
            return text_type(value)

    def _init_db(self):
        db = self._connect()
        db.execute("""
            CREATE TABLE IF NOT EXISTS translations (
                cache_key TEXT PRIMARY KEY,
                original_text TEXT,
                translated_text TEXT,
                provider TEXT,
                target_language TEXT,
                created_at INTEGER,
                used_at INTEGER
            )
        """)
        columns = [row[1] for row in db.execute("PRAGMA table_info(translations)")]
        if "used_at" not in columns:
            db.execute("ALTER TABLE translations ADD COLUMN used_at INTEGER")
        db.execute("CREATE INDEX IF NOT EXISTS translations_expiry ON translations(created_at)")
        db.commit()
        db.close()

    def make_key(self, text, mode, target_language, provider):
        raw = text.encode("utf-8") if isinstance(text, text_type) else (text or b"")
        seed = "%s|%s|%s|" % (mode, target_language, provider)
        return hashlib.sha1(seed.encode("utf-8") + raw).hexdigest()

    def get(self, key):
        now = int(time.time())
        db = self._connect()
        row = db.execute(
            "SELECT translated_text, created_at FROM translations WHERE cache_key=?", (key,)
        ).fetchone()
        if row and row[1] >= now - CACHE_TTL_SECONDS:
            db.execute("UPDATE translations SET used_at=? WHERE cache_key=?", (now, key))
            db.commit()
            db.close()
            return row[0]
        if row:
            db.execute("DELETE FROM translations WHERE cache_key=?", (key,))
            db.commit()
        db.close()
        return None

    def put(self, key, original, translated, provider, target_language):
        now = int(time.time())
        db = self._connect()
        db.execute(
            "INSERT OR REPLACE INTO translations VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self._text(key), self._text(original), self._text(translated),
             self._text(provider), self._text(target_language), now, now)
        )
        db.commit()
        db.close()

    def maintain(self):
        """Expire stale rows and evict old rows once the cache reaches its cap."""
        now = int(time.time())
        db = self._connect()
        db.execute("DELETE FROM translations WHERE created_at < ?", (now - CACHE_TTL_SECONDS,))
        db.commit()
        db.close()
        try:
            if os.path.getsize(self.path) <= CACHE_MAX_BYTES:
                return
            db = self._connect()
            target_size = CACHE_MAX_BYTES * 3 // 4
            while os.path.getsize(self.path) > target_size:
                rows = db.execute(
                    "SELECT cache_key FROM translations ORDER BY used_at ASC LIMIT 1000"
                ).fetchall()
                if not rows:
                    break
                db.executemany("DELETE FROM translations WHERE cache_key=?", rows)
                db.commit()
                db.execute("VACUUM")
            db.close()
            log("cache maintenance completed")
        except Exception as exc:
            log("cache maintenance failed: %s" % exc, "ERROR", "cache", True)
