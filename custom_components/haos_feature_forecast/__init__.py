# Updated 2025-10-30 08:05:00 CET (CET)
"""HAOS Feature Forecast integration initializer (import-safe)."""

import os
import sys
import homeassistant.util.dt as dt_util
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

DOMAIN = "haos_feature_forecast"
PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config):
    """Legacy YAML setup."""
    await _ensure_pyscript_path(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the integration."""
    await _ensure_pyscript_path(hass)

    await _notify(
        hass,
        f"Pyscript path registered for {DOMAIN} at "
        f"{dt_util.now().strftime('%Y-%m-%d %H:%M:%S')}",
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
            await _notify(hass, f"Pyscript path added: {integ_path}")
    except Exception as e:
        await _notify(hass, f"Unable to register Pyscript path: {e}", error=True)


async def _notify(hass: HomeAssistant, message: str, error: bool = False):
    """Send a persistent notification through HA's service layer."""
    title = "HAOS Feature Forecast Error" if error else "HAOS Feature Forecast"
    try:
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {"title": title, "message": message},
        )
    except Exception as e:
        print(f"[HAOS Feature Forecast] Notification failed: {e}")
