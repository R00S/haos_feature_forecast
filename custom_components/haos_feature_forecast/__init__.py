# Updated 2025-10-30 06:27:51 CET (CET)
"""HAOS Feature Forecast integration initializer."""

import sys
import os
from typing import Final
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
import homeassistant.util.dt as dt_util
from .const import DOMAIN

PLATFORMS: Final = [Platform.SENSOR]

async def async_setup(hass: HomeAssistant, config):
    """YAML-based setup (rarely used)."""
    _register_pyscript_path(hass)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up from the UI (Config Flow)."""
    _register_pyscript_path(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    hass.components.persistent_notification.create(
        "Pyscript path registered for {} at {}".format(
            DOMAIN, dt_util.now().strftime("%Y-%m-%d %H:%M:%S")
        ),
        title="HAOS Feature Forecast",
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload integration cleanly."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

def _register_pyscript_path(hass: HomeAssistant):
    """Add this integration folder to sys.path for direct imports by Pyscript."""
    integ_path = os.path.join(hass.config.path(), "custom_components", DOMAIN)
    if integ_path not in sys.path:
        sys.path.insert(0, integ_path)
