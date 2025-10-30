# Updated 2025-10-30 07:45:00 CET (CET)
"""HAOS Feature Forecast integration initializer."""

import os
import sys
import homeassistant.util.dt as dt_util
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import persistent_notification

DOMAIN = "haos_feature_forecast"
PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config):
    """Legacy YAML setup (rarely used)."""
    await _ensure_pyscript_path(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the HAOS Feature Forecast integration (Config Flow)."""
    await _ensure_pyscript_path(hass)

    persistent_notification.create(
        hass,
        f"Pyscript path registered for {DOMAIN} at "
        f"{dt_util.now().strftime('%Y-%m-%d %H:%M:%S')}",
        title="HAOS Feature Forecast",
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload integration cleanly."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _ensure_pyscript_path(hass: HomeAssistant):
    """Make this integration visible to Pyscript without copying files."""
    integ_path = os.path.join(hass.config.path(), "custom_components", DOMAIN)
    if integ_path not in sys.path:
        sys.path.insert(0, integ_path)

    try:
        pys_app = hass.data.get("pyscript")
        if pys_app and hasattr(pys_app, "add_path"):
            pys_app.add_path(integ_path)
            persistent_notification.create(
                hass,
                f"Pyscript path added: {integ_path}",
                title="HAOS Feature Forecast",
            )
    except Exception as e:
        persistent_notification.create(
            hass,
            f"Unable to register Pyscript path: {e}",
            title="HAOS Feature Forecast Error",
        )
