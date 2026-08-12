import os
import sys
import tempfile
import types
import unittest


PYTHON_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rootfs", "usr", "lib", "enigma2", "python"))
sys.path.insert(0, PYTHON_ROOT)

components = types.ModuleType("Components")
components.__path__ = [os.path.join(PYTHON_ROOT, "Components")]
config_module = types.ModuleType("Components.config")


class Node(object):
    pass


class YesNo(object):
    def __init__(self, default=False):
        self.value = default


config_module.config = Node()
config_module.config.plugins = Node()
config_module.ConfigSubsection = Node
config_module.ConfigYesNo = YesNo
sys.modules["Components"] = components
sys.modules["Components.config"] = config_module

converter_package = types.ModuleType("Components.Converter")
converter_package.__path__ = [os.path.join(PYTHON_ROOT, "Components", "Converter")]
converter_module = types.ModuleType("Components.Converter.Converter")
element_module = types.ModuleType("Components.Element")


class Converter(object):
    CHANGED_ALL = 0

    def __init__(self, converter_type):
        self.type = converter_type


def cached(function):
    return function


converter_module.Converter = Converter
element_module.cached = cached
sys.modules["Components.Converter"] = converter_package
sys.modules["Components.Converter.Converter"] = converter_module
sys.modules["Components.Element"] = element_module

renderer_package = types.ModuleType("Components.Renderer")
renderer_package.__path__ = [os.path.join(PYTHON_ROOT, "Components", "Renderer")]
event_list_renderer = types.ModuleType("Components.Renderer.EventListDisplay")


class EventListDisplay(object):
    pass


event_list_renderer.EventListDisplay = EventListDisplay
sys.modules["Components.Renderer"] = renderer_package
sys.modules["Components.Renderer.EventListDisplay"] = event_list_renderer

enigma = types.ModuleType("enigma")


class Timer(object):
    def __init__(self):
        self.callback = []

    def start(self, *args):
        pass

    def stop(self):
        pass


class Container(object):
    def __init__(self):
        self.appClosed = []
        self.last_command = None

    def execute(self, *args):
        self.last_command = args[0]
        return 0

    def kill(self):
        pass


enigma.eTimer = Timer
enigma.eConsoleAppContainer = Container
sys.modules["enigma"] = enigma

from Plugins.Extensions.e2EPG import cache as cache_module
from Plugins.Extensions.e2EPG import gemini as gemini_module
from Plugins.Extensions.e2EPG import language
from Plugins.Extensions.e2EPG import service as service_module
from Plugins.Extensions.e2EPG import compat
from Components.Converter.e2EPG import _enigma_text
from Components.Renderer.e2EPGEventListDisplay import _anchor_after_time


class CoreTests(unittest.TestCase):
    def test_epg_next_rtl_title_is_ltr_column_anchored(self):
        value = _anchor_after_time(u"برنامه بعدی")
        self.assertEqual(value, u"\u202aبرنامه بعدی\u202c")
        if sys.version_info[0] == 2:
            encoded = _anchor_after_time(u"برنامه بعدی".encode("utf-8"))
            self.assertIsInstance(encoded, str)
            self.assertEqual(encoded.decode("utf-8"), value)

    def test_compat_patches_standard_and_modular_screens(self):
        skin = '''<skin>
          <screen name="InfoBar"><convert type="EventName">Name</convert></screen>
          <screen name='ChannelSelection'>
            <convert type="EventName">FullDescription</convert>
            <widget render="EventListDisplay" />
          </screen>
        </skin>'''
        patched, stats = compat.patch_text(skin)
        self.assertIn('<convert type="e2EPG">Name</convert>', patched)
        self.assertIn('<convert type="e2EPG">FullDescription</convert>', patched)
        self.assertIn('render="e2EPGEventListDisplay"', patched)
        self.assertEqual(stats, {"infobar": 1, "channel": 1, "next": 1})

    def test_compat_is_idempotent_and_screen_scoped(self):
        skin = '''<skin>
          <screen name="EPGSelection"><convert type="EventName">Name</convert></screen>
          <screen name="InfoBar"><convert type="EventName">Name</convert></screen>
        </skin>'''
        once, stats = compat.patch_text(skin)
        twice, second_stats = compat.patch_text(once)
        self.assertEqual(once, twice)
        self.assertEqual(second_stats, {"infobar": 0, "channel": 0, "next": 0})
        self.assertIn('<screen name="EPGSelection"><convert type="EventName">Name</convert>', once)

    def test_compat_runtime_scan_patches_new_modular_skin(self):
        root = tempfile.mkdtemp(prefix="e2epg-skins-")
        module = os.path.join(root, "NewSkin", "parts")
        os.makedirs(module)
        skin_path = os.path.join(module, "channels.xml")
        with open(skin_path, "wb") as skin:
            skin.write(b'<screen name="ChannelSelection"><widget render="EventListDisplay" /></screen>')
        old_config = compat.CONFIG_DIR
        old_state = compat.STATE_FILE
        old_backup = compat.BACKUP_DIR
        compat.CONFIG_DIR = os.path.join(root, "state")
        compat.STATE_FILE = os.path.join(compat.CONFIG_DIR, "skin-compat.json")
        compat.BACKUP_DIR = os.path.join(compat.CONFIG_DIR, "skin-backups")
        try:
            result = compat.scan_and_patch(root)
            self.assertEqual(result["changed"], 1)
            with open(skin_path, "rb") as skin:
                self.assertIn(b'e2EPGEventListDisplay', skin.read())
            self.assertTrue(os.path.isfile(compat.STATE_FILE))
            self.assertEqual(compat.scan_and_patch(root)["changed"], 0)
        finally:
            compat.CONFIG_DIR = old_config
            compat.STATE_FILE = old_state
            compat.BACKUP_DIR = old_backup

    def test_language_filter(self):
        self.assertTrue(language.should_translate(u"English movie"))
        self.assertTrue(language.should_translate(u"فيلم عربي"))
        self.assertTrue(language.should_translate(u"Русский фильм"))
        self.assertTrue(language.should_translate(u"中文节目"))
        self.assertFalse(language.should_translate(u"فیلم فارسی"))
        self.assertFalse(language.should_translate(u"سلام دنیا"))
        self.assertFalse(language.should_translate(u"2026 - 12:30"))

    def test_dreamos_text_boundary(self):
        value = _enigma_text(u"سلام دنیا")
        if sys.version_info[0] == 2:
            self.assertIsInstance(value, str)
            self.assertEqual(value.decode("utf-8"), u"سلام دنیا")
        else:
            self.assertEqual(value, u"سلام دنیا")

    def test_cache_round_trip(self):
        root = tempfile.mkdtemp(prefix="pepg-test-")
        old_get_path = cache_module.get_cache_path
        cache_module.get_cache_path = lambda: os.path.join(root, "cache.db")
        try:
            cache = cache_module.TranslationCache()
            key = cache.make_key(u"Hello", "name", "fa", "test")
            cache.put(key, u"Hello", u"سلام", "test", "fa")
            self.assertEqual(cache.get(key), u"سلام")
            cache.put(key, "Hello", u"سلام".encode("utf-8"), "test", "fa")
            self.assertEqual(cache.get(key), u"سلام")
        finally:
            cache_module.get_cache_path = old_get_path

    def test_jobs_are_serial_and_refresh(self):
        class MemoryCache(object):
            values = {}

            def make_key(self, text, mode, target, provider):
                return text

            def get(self, key):
                return self.values.get(key)

            def put(self, key, original, value, provider, target):
                self.values[key] = value

            def maintain(self):
                pass

        class Job(object):
            made = []

            def __init__(self, text, callback):
                self.callback = callback
                self.made.append(self)

            def start(self):
                pass

        old_cache = service_module.TranslationCache
        old_job = service_module.GeminiTranslateJob
        old_ready = service_module.engine_ready
        service_module.TranslationCache = MemoryCache
        service_module.GeminiTranslateJob = Job
        service_module.engine_ready = lambda: True
        service_module.config.plugins.persianepg.enabled.value = True
        try:
            service = service_module.e2EPGService()
            refreshed = []
            service.get_cached_or_queue(None, 0, u"One", lambda: refreshed.append(1))
            service.get_cached_or_queue(None, 0, u"Two", lambda: refreshed.append(2))
            self.assertEqual(len(Job.made), 1)
            self.assertEqual(len(service.queue), 1)
            Job.made[0].callback(True, u"یک", None)
            self.assertEqual(refreshed, [1])
            self.assertEqual(len(Job.made), 2)
            Job.made[1].callback(True, u"دو", None)
            self.assertEqual(refreshed, [1, 2])
            self.assertIsNone(service.active_job)
            self.assertFalse(service.pending)
        finally:
            service_module.TranslationCache = old_cache
            service_module.GeminiTranslateJob = old_job
            service_module.engine_ready = old_ready

    def test_api_key_is_not_in_process_arguments(self):
        secret = "test_secret_key_abcdefghijklmnopqrstuvwxyz"
        old_read_key = gemini_module.read_api_key
        gemini_module.read_api_key = lambda: secret
        callbacks = []
        job = gemini_module.GeminiTranslateJob(u"Hello", lambda *args: callbacks.append(args))
        try:
            job.start()
            self.assertTrue(job.container.last_command)
            self.assertNotIn(secret, job.container.last_command)
            config_path = [path for path in job.paths if path.endswith(".curl")][0]
            payload_path = [path for path in job.paths if path.endswith(".json")][0]
            with open(config_path, "rb") as config_file:
                self.assertIn(secret.encode("ascii"), config_file.read())
            with open(payload_path, "rb") as payload_file:
                payload = payload_file.read()
            self.assertNotIn(secret.encode("ascii"), payload)
            self.assertIn(b"Hello", payload)
        finally:
            job._cleanup()
            gemini_module.read_api_key = old_read_key


if __name__ == "__main__":
    unittest.main()
