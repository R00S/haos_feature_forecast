# Updated 2025-10-30 11:50:00 CET (CET)
"""HAOS Feature Forecast integration initializer."""

import os
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.util import dt as dt_util
from .const import DOMAIN

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: dict):
    """Legacy YAML setup (normally unused)."""
    _register_service(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up integration from Config Flow."""
    _register_service(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await _notify(hass, f"HAOS Feature Forecast loaded at {dt_util.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the integration cleanly."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _register_service(hass: HomeAssistant):
    """Register the pyscript-style update service."""

    async def handle_service(call):
        await _notify(hass, f"Forecast fetch simulated at {dt_util.now().strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            from . import fetch_haos_features
            await fetch_haos_features.main(hass)
        except Exception as e:
            await _notify(hass, f"Error running fetch_haos_features: {e}")

    hass.services.async_register(DOMAIN, "update_forecast", handle_service)


async def _notify(hass: HomeAssistant, message: str):
    """Show a persistent notification."""
    await hass.services.async_call(
        "persistent_notification",
        "create",
        {"title": "HAOS Feature Forecast", "message": message},
    )
