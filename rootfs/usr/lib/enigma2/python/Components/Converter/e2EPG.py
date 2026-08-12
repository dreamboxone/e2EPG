# -*- coding: utf-8 -*-
from Components.Converter.Converter import Converter
from Components.Element import cached

try:
    text_type = unicode
except NameError:
    text_type = str


def _enigma_text(value):
    """DreamOS Python 2 SWIG labels require UTF-8 str, not unicode."""
    if value is None:
        return ""
    if isinstance(value, text_type) and text_type is not str:
        return value.encode("utf-8")
    return value


class e2EPG(Converter, object):
    NAME = 0
    SHORT = 1
    EXTENDED = 2
    FULL = 3

    def __init__(self, type):
        Converter.__init__(self, type)
        wanted = (type or "Name").lower()
        if wanted in ("short", "shortdescription"):
            self.mode = self.SHORT
        elif wanted in ("extended", "extendeddescription"):
            self.mode = self.EXTENDED
        elif wanted in ("full", "fulldescription"):
            self.mode = self.FULL
        else:
            self.mode = self.NAME

    @cached
    def getText(self):
        event = self.source.event
        if event is None:
            return ""
        original = self._get_original(event)
        if not original:
            return ""
        try:
            from Plugins.Extensions.e2EPG.service import get_service
            translated = get_service().get_cached_or_queue(event, self.mode, original, self._translation_ready)
            return _enigma_text(translated or original)
        except Exception as exc:
            try:
                from Plugins.Extensions.e2EPG.config import log
                log("converter fallback: %s" % exc, "ERROR", "converter", True)
            except Exception:
                pass
            return _enigma_text(original)

    text = property(getText)

    def _translation_ready(self):
        self.changed((self.CHANGED_ALL,))

    def _get_original(self, event):
        if self.mode == self.SHORT:
            return event.getShortDescription() or ""
        if self.mode == self.EXTENDED:
            return event.getExtendedDescription() or ""
        if self.mode == self.FULL:
            short = event.getShortDescription() or ""
            extended = event.getExtendedDescription() or ""
            if short and extended:
                return short + "\n" + extended
            return short or extended
        return event.getEventName() or ""
