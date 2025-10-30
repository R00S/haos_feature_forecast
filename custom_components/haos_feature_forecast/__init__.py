# Updated 2025-10-30 09:20:00 CET (CET)
"""HAOS Feature Forecast integration — run Pyscript directly from component path."""

import os
import sys
import importlib
import homeassistant.util.dt as dt_util
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

DOMAIN = "haos_feature_forecast"
PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config):
    """Legacy YAML setup."""
    await _ensure_pyscript_import(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the integration and make Pyscript reload the file in-place."""
    await _ensure_pyscript_import(hass)

    await _notify(
        hass,
        f"Pyscript import path ready for {DOMAIN} at {dt_util.now().strftime('%Y-%m-%d %H:%M:%S')}",
    )

    try:
        # Reload Pyscript and import the file directly
        await hass.services.async_call("pyscript", "reload")
        importlib.invalidate_caches()
        importlib.import_module(f"custom_components.{DOMAIN}.fetch_haos_features")
        await _notify(hass, "Fetched module loaded directly into Pyscript context.")
    except Exception as e:
        await _notify(hass, f"Direct import failed: {e}", error=True)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload integration cleanly."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _ensure_pyscript_import(hass: HomeAssistant):
    """Ensure Pyscript can import our module directly from this folder."""
    integ_path = os.path.join(hass.config.path(), "custom_components", DOMAIN)
    if integ_path not in sys.path:
        sys.path.insert(0, integ_path)
    init_file = os.path.join(integ_path, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w", encoding="utf-8") as f:
            f.write(f"# auto-generated to make {DOMAIN} importable\n")
    pys_app = hass.data.get("pyscript")
    if pys_app and hasattr(pys_app, "add_path"):
        pys_app.add_path(integ_path)
        await _notify(hass, f"Pyscript import path added: {integ_path}")


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
