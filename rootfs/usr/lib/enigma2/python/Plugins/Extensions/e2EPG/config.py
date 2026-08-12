# -*- coding: utf-8 -*-
import os
import re
from Components.config import ConfigSubsection, ConfigYesNo, config

from .logger import log

PLUGIN_NAME = "e2EPG"
PLUGIN_VERSION = "0.5.3"
CONFIG_DIR = "/etc/enigma2/e2EPG"
API_KEY_FILE = "/root/apikey.txt"
TARGET_LANGUAGE = "fa"
SOURCE_LANGUAGE = "auto"
PROVIDER = "gemini-3.1-flash-lite"
CACHE_MAX_BYTES = 100 * 1024 * 1024
CACHE_TTL_SECONDS = 30 * 24 * 60 * 60
REQUEST_TIMEOUT = 25
GEMINI_ENDPOINT = ("https://generativelanguage.googleapis.com/v1beta/models/"
                   "gemini-3.1-flash-lite:generateContent")

if not hasattr(config.plugins, "persianepg"):
    config.plugins.persianepg = ConfigSubsection()
if not hasattr(config.plugins.persianepg, "enabled"):
    config.plugins.persianepg.enabled = ConfigYesNo(default=False)


def get_data_dir():
    for base in ("/media/hdd", "/data", "/media/usb"):
        if os.path.isdir(base) and os.access(base, os.W_OK):
            path = os.path.join(base, PLUGIN_NAME)
            if not os.path.isdir(path):
                try:
                    os.makedirs(path)
                except Exception:
                    continue
            return path
    if not os.path.isdir(CONFIG_DIR):
        try:
            os.makedirs(CONFIG_DIR)
        except Exception:
            pass
    return CONFIG_DIR


def get_cache_path():
    return os.path.join(get_data_dir(), "cache.db")


def read_api_key():
    try:
        raw = open(API_KEY_FILE, "rb").read(4096).strip()
        key = raw.decode("utf-8", "replace") if hasattr(raw, "decode") else raw
        if (not key or len(key) < 20 or len(key) > 512 or
                not re.match(r"^[A-Za-z0-9._-]+$", key)):
            return ""
        return key
    except Exception:
        return ""


def engine_ready():
    return bool(read_api_key())
