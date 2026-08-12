# -*- coding: utf-8 -*-
import time

from enigma import eTimer

from .cache import TranslationCache
from .config import PROVIDER, TARGET_LANGUAGE, config, engine_ready, log
from .gemini import GeminiTranslateJob
from .language import should_translate


class e2EPGService(object):
    BATCH_SIZE = 20
    def __init__(self):
        self.cache = TranslationCache()
        self.pending = {}
        self.queue = []
        self.active_job = None
        self.blocked_until = 0
        self.retry_timer = eTimer()
        self.signal_connections = []
        self._connect_timer(self.retry_timer, self._resume)
        self.maintenance_timer = eTimer()
        self._connect_timer(self.maintenance_timer, self._maintain)
        self.maintenance_timer.start(120000, False)
        log("service started", component="service")

    def _connect_timer(self, timer, callback):
        signal = getattr(timer, "timeout", None) or timer.callback
        if hasattr(signal, "append"):
            signal.append(callback)
        else:
            self.signal_connections.append(signal.connect(callback))

    def get_cached_or_queue(self, event, mode, original, refresh=None):
        if not config.plugins.persianepg.enabled.value:
            return original
        if not should_translate(original):
            return original
        key = self.cache.make_key(original, mode, TARGET_LANGUAGE, PROVIDER)
        cached_text = self.cache.get(key)
        if cached_text:
            log("cache hit id=%s mode=%s" % (key[:10], mode), "DEBUG", "service")
            return cached_text
        if not engine_ready():
            log("engine unavailable; returning original", "DEBUG", "service")
            return original
        if time.time() < self.blocked_until:
            return original
        if key in self.pending:
            if refresh is not None and refresh not in self.pending[key]["callbacks"]:
                self.pending[key]["callbacks"].append(refresh)
            return original
        self.pending[key] = {"callbacks": [refresh] if refresh is not None else []}
        if len(self.queue) >= 50:
            dropped_key, dropped_original = self.queue.pop(0)
            self.pending.pop(dropped_key, None)
            log("queue limit reached; dropped id=%s" % dropped_key[:10], "WARNING", "service")
        self.queue.append((key, original))
        log("queued id=%s mode=%s chars=%s depth=%s" %
            (key[:10], mode, len(original), len(self.queue)), "DEBUG", "service")
        self._start_next()
        return original

    def _start_next(self):
        if self.active_job is not None or not self.queue or time.time() < self.blocked_until:
            return
        batch = []
        while self.queue and len(batch) < self.BATCH_SIZE:
            batch.append(self.queue.pop(0))
        originals = [item[1] for item in batch]
        self.active_job = GeminiTranslateJob(
            originals if len(originals) > 1 else originals[0],
            lambda ok, value, status, items=batch: self._done_batch(items, ok, value, status)
        )
        log("translation batch start count=%s chars=%s" %
            (len(batch), sum(len(value) for value in originals)), "DEBUG", "service")
        self.active_job.start()

    def _done_batch(self, batch, ok, value, status=None):
        self.active_job = None
        values = value if ok and isinstance(value, list) else [value]
        if ok and len(values) != len(batch):
            ok = False
            values = ["Gemini returned an invalid translation batch"]
        callbacks = []
        for index, (key, original) in enumerate(batch):
            item = self.pending.pop(key, {"callbacks": []})
            callbacks.extend(item["callbacks"])
            if not ok:
                continue
            try:
                translated = values[index]
                self.cache.put(key, original, translated, PROVIDER, TARGET_LANGUAGE)
                log("translation success id=%s output_chars=%s" %
                    (key[:10], len(translated)), "DEBUG", "service")
            except Exception as exc:
                log("cache write failed: %s" % exc, "ERROR", "cache", True)
        if not ok:
            log("translation failed id=%s api_status=%s error=%s" %
                (batch[0][0][:10], status, values[0]), "ERROR", "gemini")
            delay = 300 if status in (400, 401, 403) else 60 if status == 429 else 15
            self.blocked_until = time.time() + delay
            self.retry_timer.start(delay * 1000, True)
        for callback in callbacks:
            try:
                callback()
            except Exception:
                log("converter refresh callback failed", "ERROR", "service", True)
        self._start_next()

    def _resume(self):
        self.blocked_until = 0
        log("request cooldown ended", "DEBUG", "service")
        self._start_next()

    def _maintain(self):
        try:
            if config.plugins.persianepg.enabled.value:
                self.cache.maintain()
        except Exception:
            log("scheduled cache maintenance failed", "ERROR", "cache", True)
        finally:
            self.maintenance_timer.start(6 * 60 * 60 * 1000, False)


_service = None


def get_service():
    global _service
    if _service is None:
        _service = e2EPGService()
    return _service
