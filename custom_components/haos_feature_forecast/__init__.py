# Updated 2025-10-27 21:55:12 CET (CET)
"""HAOS Feature Forecast integration initializer."""

from __future__ import annotations
import os
import shutil
from typing import Final

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
import homeassistant.util.dt as dt_util
from .const import DOMAIN

PLATFORMS: Final = [Platform.SENSOR]

PYSCRIPT_FILES: Final[list[str]] = [
    "fetch_haos_features.py",
]


async def async_setup(hass: HomeAssistant, config):
    """Run on every HA start, even without a config entry."""
    await _ensure_pyscript_files(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up from the UI (config flow)."""
    await _ensure_pyscript_files(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _ensure_pyscript_files(hass: HomeAssistant):
    """Copy declared Pyscript files into /config/pyscript."""
    pyscript_dir = os.path.join(hass.config.path(), "pyscript")
    if not os.path.exists(pyscript_dir):
        os.makedirs(pyscript_dir)

    for filename in PYSCRIPT_FILES:
        source = os.path.join(hass.config.path(), "custom_components", DOMAIN, filename)
        dest = os.path.join(pyscript_dir, filename)
        try:
            if not os.path.exists(source):
                hass.components.persistent_notification.create(
                    f"Missing source file: {filename} in {source}",
                    title="HAOS Feature Forecast Error",
                )
                continue

            if (not os.path.exists(dest)) or (os.path.getmtime(source) > os.path.getmtime(dest)):
                shutil.copy2(source, dest)
                hass.components.persistent_notification.create(
                    f"Copied {filename} to /config/pyscript/ at "
                    f"{dt_util.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    title="HAOS Feature Forecast",
                )
        except Exception as e:
            hass.components.persistent_notification.create(
                f"Failed to copy {filename}: {e}",
                title="HAOS Feature Forecast Error",
            )
