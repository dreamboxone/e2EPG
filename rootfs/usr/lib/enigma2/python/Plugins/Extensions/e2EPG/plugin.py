# -*- coding: utf-8 -*-
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.config import configfile, getConfigListEntry
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from enigma import eTimer
from .config import API_KEY_FILE, PLUGIN_VERSION, config, engine_ready, log
from .logger import runtime_summary

_compat_timer = None
_compat_connections = []


class e2EPGSetup(Screen, ConfigListScreen):
    skin = """
        <screen name="e2EPGSetup" position="center,center" size="820,390" title="e2EPG">
            <widget name="config" position="35,50" size="750,45" scrollbarMode="showOnDemand" />
            <widget name="status" position="35,125" size="750,70" font="Regular;24" halign="center" valign="center" />
            <widget name="plugin_info" position="35,205" size="750,38" font="Regular;22" halign="center" valign="center" />
            <widget name="key_red" position="35,280" size="220,45" font="Regular;24" foregroundColor="red" />
            <widget name="key_green" position="300,280" size="220,45" font="Regular;24" foregroundColor="green" />
            <widget name="key_yellow" position="565,280" size="220,45" font="Regular;24" foregroundColor="yellow" />
        </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.list = [
            getConfigListEntry("Enable Persian EPG translation", config.plugins.persianepg.enabled),
        ]
        ConfigListScreen.__init__(self, self.list, session=session)
        self["status"] = Label("")
        self["plugin_info"] = Label("Version %s  |  Telegram: t.me/RouteKernel1" % PLUGIN_VERSION)
        self["key_red"] = Label("Cancel")
        self["key_green"] = Label("Save")
        self["key_yellow"] = Label("About")
        self["actions"] = ActionMap(["ColorActions", "SetupActions"], {
            "red": self.cancel,
            "green": self.save,
            "yellow": self.about,
            "cancel": self.cancel,
            "ok": self.save,
        }, -2)
        self._update_status()
        log("setup opened; %s" % runtime_summary(), component="plugin")

    def _update_status(self):
        if engine_ready():
            self["status"].setText("Gemini API key is ready. Multilingual translation is available.")
        else:
            self["status"].setText("Gemini API key is missing or invalid in /root/apikey.txt.")

    def save(self):
        for item in self["config"].list:
            item[1].save()
        configfile.save()
        if config.plugins.persianepg.enabled.value and not engine_ready():
            log("plugin enabled but Gemini API key is unavailable", "WARNING", "plugin")
            self.session.open(
                MessageBox,
                "Gemini API key was not found.\n\n"
                "Put only the API key on one line in:\n"
                "/root/apikey.txt\n\n"
                "Recommended file permissions: 600.",
                MessageBox.TYPE_WARNING,
            )
            return
        self.close()

    def cancel(self):
        for item in self["config"].list:
            item[1].cancel()
        self.close()

    def about(self):
        self.session.open(
            MessageBox,
            "e2EPG %s\n\n"
            "Gemini-powered multilingual EPG translation to Persian.\n\n"
            "API key: %s\n\n"
            "Telegram: t.me/RouteKernel1\n"
            "YouTube: youtube.com/@Routeketnel\n"
            "GitHub: github.com/dreamboxone" % (PLUGIN_VERSION, API_KEY_FILE),
            MessageBox.TYPE_INFO,
        )



def main(session, **kwargs):
    session.open(e2EPGSetup)


def session_start(reason, **kwargs):
    if reason == 0:
        log("Enigma2 session started; %s" % runtime_summary(), component="startup")
        from .servicelist import install
        install()
        _start_compat_monitor()


def _compat_scan():
    try:
        from .compat import scan_and_patch
        scan_and_patch()
    except Exception:
        log("scheduled compatibility scan failed", "ERROR", "compat", True)
    finally:
        if _compat_timer is not None:
            _compat_timer.start(10 * 60 * 1000, True)


def _start_compat_monitor():
    global _compat_timer
    if _compat_timer is not None:
        return
    _compat_timer = eTimer()
    signal = getattr(_compat_timer, "timeout", None) or _compat_timer.callback
    if hasattr(signal, "append"):
        signal.append(_compat_scan)
    else:
        _compat_connections.append(signal.connect(_compat_scan))
    # Keep startup and, most importantly, shutdown free of filesystem scans.
    # The first normal-runtime scan runs after Enigma2 has settled.
    _compat_timer.start(30 * 1000, True)
    log("compatibility monitor scheduled", component="compat")


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="e2EPG",
            description="Gemini multilingual EPG translation to Persian",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            fnc=main,
            icon="plugin.png"
        ),
        PluginDescriptor(
            where=PluginDescriptor.WHERE_SESSIONSTART,
            fnc=session_start
        ),
    ]
