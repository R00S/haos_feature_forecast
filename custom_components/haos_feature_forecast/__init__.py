# Updated 2025-10-27 22:59:19 CET (CET)
"""HAOS Feature Forecast integration initializer."""

from __future__ import annotations
import os, shutil
from typing import Final
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
import homeassistant.util.dt as dt_util
from .const import DOMAIN

PLATFORMS: Final = [Platform.SENSOR]
PYSCRIPT_FILES: Final[list[str]] = ["fetch_haos_features.py"]

async def async_setup(hass: HomeAssistant, config):
    await _ensure_pyscript_files(hass)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    await _ensure_pyscript_files(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def _ensure_pyscript_files(hass: HomeAssistant):
    pyscript_dir = os.path.join(hass.config.path(), "pyscript")
    os.makedirs(pyscript_dir, exist_ok=True)
    for f in PYSCRIPT_FILES:
        src = os.path.join(hass.config.path(), "custom_components", DOMAIN, f)
        dst = os.path.join(pyscript_dir, f)
        if not os.path.exists(src):
            hass.components.persistent_notification.create(f"Missing source {src}", title="HAOS Feature Forecast Error")
            continue
        try:
            if (not os.path.exists(dst)) or (os.path.getmtime(src) > os.path.getmtime(dst)):
                shutil.copy2(src, dst)
                hass.components.persistent_notification.create(
                    f"Copied {f} to /config/pyscript/ at {dt_util.now().strftime("%Y-%m-%d %H:%M:%S")}",
                    title="HAOS Feature Forecast",
                )
        except Exception as e:
            hass.components.persistent_notification.create(f"Copy failed: {e}", title="HAOS Feature Forecast Error")
