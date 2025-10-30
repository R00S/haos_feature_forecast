# Updated 2025-10-30 10:10:00 CET (CET)
"""HAOS Feature Forecast integration — exposes native HA service."""

import asyncio
import os
import sys
import importlib
import homeassistant.util.dt as dt_util
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

DOMAIN = "haos_feature_forecast"
PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config):
    """Legacy YAML setup."""
    await _register_service(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """UI config flow setup."""
    await _register_service(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await _notify(hass, f"{DOMAIN} service registered at {dt_util.now().strftime('%H:%M:%S')}")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Allow GUI removal."""
    hass.services.async_remove(DOMAIN, "update_forecast")
    hass.data.pop(DOMAIN, None)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _register_service(hass: HomeAssistant):
    """Expose haos_feature_forecast.update_forecast service."""
    async def handle_service(call: ServiceCall):
        msg = f"Manual forecast update triggered at {dt_util.now().strftime('%H:%M:%S')}"
        await _notify(hass, msg)

        # Try importing your logic dynamically
        try:
            module_name = f"custom_components.{DOMAIN}.fetch_haos_features"
            importlib.invalidate_caches()
            module = importlib.import_module(module_name)
            if hasattr(module, "main"):
                await asyncio.create_task(module.main(hass))
                await _notify(hass, "Forecast update completed.")
            else:
                await _notify(hass, f"No 'main(hass)' found in {module_name}", error=True)
        except Exception as e:
            await _notify(hass, f"Error running forecast: {e}", error=True)

    hass.services.async_register(DOMAIN, "update_forecast", handle_service)


async def _notify(hass: HomeAssistant, message: str, error: bool = False):
    """Send a persistent notification."""
    title = "HAOS Feature Forecast Error" if error else "HAOS Feature Forecast"
    try:
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {"title": title, "message": message},
        )
    except Exception as e:
        print(f"[HAOS Feature Forecast] Notification failed: {e}")
