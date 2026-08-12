# -*- coding: utf-8 -*-
"""Translate EPG labels produced directly by DreamOS ServiceList."""
from .config import config, log
from .service import get_service

_installed = False
try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)


def install():
    global _installed
    if _installed:
        return
    try:
        from Components.ServiceList import ServiceList
        original = ServiceList.buildOptionEntry

        def translated_entry(instance, service, **args):
            result = original(instance, service, **args)
            if not config.plugins.persianepg.enabled.value:
                return result
            try:
                info = instance.service_center.info(service)
                event = info and info.getEvent(service)
                if event is None:
                    return result
                names = [(event.getEventName() or "", 0)]
                try:
                    from enigma import eEPGCache
                    next_event = eEPGCache.getInstance().lookupEventTime(service, -1, 1)
                    if next_event:
                        names.append((next_event.getEventName() or "", 0))
                except Exception:
                    pass

                refresh = getattr(instance, "invalidate", None)
                if refresh is None:
                    refresh = getattr(getattr(instance, "l", None), "invalidate", None)
                replacements = {}
                for name, mode in names:
                    if name:
                        replacements[name] = get_service().get_cached_or_queue(
                            event, mode, name, refresh)
                if not replacements:
                    return result
                output = []
                for row in result:
                    if not isinstance(row, tuple):
                        output.append(row)
                        continue
                    values = list(row)
                    for index, value in enumerate(values):
                        if not isinstance(value, string_types):
                            continue
                        for source, translated in replacements.items():
                            if translated and source in value:
                                display = translated
                                if isinstance(value, str) and not isinstance(display, str):
                                    display = display.encode("utf-8")
                                values[index] = value.replace(source, display)
                    output.append(tuple(values))
                return output
            except Exception as exc:
                log("ServiceList translation fallback: %s" % exc,
                    "ERROR", "servicelist", True)
                return result

        ServiceList.buildOptionEntry = translated_entry
        _installed = True
        log("ServiceList EPG translation hook installed", component="servicelist")
    except Exception:
        log("unable to install ServiceList translation hook",
            "ERROR", "servicelist", True)
