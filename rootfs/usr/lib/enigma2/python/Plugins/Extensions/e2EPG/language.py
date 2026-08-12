# -*- coding: utf-8 -*-
import re

try:
    text_type = unicode
except NameError:
    text_type = str

# Arabic remains eligible for translation. Persian-specific letters and common
# Persian words prevent already-Persian EPG text being paraphrased.
PERSIAN_MARKERS = re.compile(u"[\u067e\u0686\u0698\u06af\u06a9\u06cc\u06c0]")
PERSIAN_WORDS = re.compile(u"(?:^|[\\s،؛؟])(?:این|است|های|برای|یک|فیلم|سریال|برنامه|قسمت|شبکه)(?:$|[\\s،؛؟])")


def has_persian_marker(text):
    if not isinstance(text, text_type):
        try:
            text = text.decode("utf-8")
        except Exception:
            return False
    return bool(PERSIAN_MARKERS.search(text) or PERSIAN_WORDS.search(text))


def should_translate(text):
    if not text or has_persian_marker(text):
        return False
    if not isinstance(text, text_type):
        try:
            text = text.decode("utf-8")
        except Exception:
            return False
    return any(character.isalpha() for character in text)
