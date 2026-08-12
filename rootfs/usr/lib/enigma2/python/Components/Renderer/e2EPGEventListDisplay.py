# -*- coding: utf-8 -*-
"""Translate title columns supplied to DreamOS EventListDisplay."""
from Components.Renderer.EventListDisplay import EventListDisplay

try:
    text_type = unicode
except NameError:
    text_type = str


def _anchor_after_time(value):
    """Keep a Persian title at the left edge of its LTR EPG title column."""
    if not value:
        return value
    is_bytes = isinstance(value, str) and text_type is not str
    text = value.decode("utf-8", "replace") if is_bytes else value
    # LRE/PDF controls paragraph placement only. Persian glyph shaping and
    # character order remain RTL, while the run begins next to the time column.
    anchored = u"\u202a" + text + u"\u202c"
    return anchored.encode("utf-8") if is_bytes else anchored


class _TranslatedSource(object):
    def __init__(self, source, renderer):
        self._source = source
        self._renderer = renderer

    def __getattr__(self, name):
        return getattr(self._source, name)

    def getContent(self):
        content = self._source.getContent()
        try:
            from Plugins.Extensions.e2EPG.service import get_service
            service = get_service()
            output = []
            for row in content:
                values = list(row)
                # EventListDisplay convention: column 0 is time and column 1
                # is the programme title. Preserve every other source field.
                if len(values) > 1 and values[1]:
                    translated = service.get_cached_or_queue(
                        None, 0, values[1], self._renderer._translation_ready)
                    if translated:
                        if isinstance(values[1], str) and not isinstance(translated, str):
                            translated = translated.encode("utf-8")
                        values[1] = _anchor_after_time(translated)
                output.append(tuple(values))
            return output
        except Exception as exc:
            try:
                from Plugins.Extensions.e2EPG.config import log
                log("EPG Next renderer fallback: %s" % exc,
                    "ERROR", "eventlist", True)
            except Exception:
                pass
            return content


class e2EPGEventListDisplay(EventListDisplay):
    def pull_updates(self):
        source = self.source
        self.source = _TranslatedSource(source, self)
        try:
            EventListDisplay.pull_updates(self)
        finally:
            self.source = source

    def _translation_ready(self):
        self.pull_updates()
