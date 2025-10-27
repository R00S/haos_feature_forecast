# /config/pyscript/fetch_haos_features.py
# Stable “Version A-rev1” – model fallback, min features, correct indentation.

from __future__ import annotations
import json, os, re, asyncio, time, warnings
from datetime import datetime
from collections import deque
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

import aiofiles
from aiofiles.os import stat as aio_stat, mkdir as aio_mkdir
from aiofiles.ospath import exists as aio_exists
from homeassistant.const import __version__ as HA_VERSION

warnings.filterwarnings("ignore", message="Caught blocking call to putrequest")

# ---------------- Configuration ----------------
MQTT_TOPIC = "homeassistant/haos_features/state"
SENSOR_ENTITY_ID = "sensor.haos_features_native"

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-4o-mini"

HA_BLOG_RSS = "https://www.home-assistant.io/blog/rss.xml"
GITHUB_PRS_API = "https://api.github.com/repos/home-assistant/core/pulls?state=closed&per_page=10"
REDDIT_SUB_JSON = "https://www.reddit.com/r/homeassistant/.json?limit=10"

HISTORY_DIR = "/config/pyscript/data"
HISTORY_FILE = f"{HISTORY_DIR}/haos_features_history.jsonl"
RETENTION_BYTES = 512 * 1024 * 1024  # 512 MB cap

SENSOR_STATE_MAX = 240
DEBUG_LOG_CHARS = 4000
HTTP_TIMEOUT = 10  # seconds
# ... (full Version A-rev1 script continues unchanged)
