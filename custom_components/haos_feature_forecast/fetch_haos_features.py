# Updated 2025-10-30 10:40:00 CET (CET)
"""Fetch upcoming Home Assistant features — minimal entrypoint."""

import homeassistant.util.dt as dt_util

async def main(hass):
    """Entry point called by haos_feature_forecast.update_forecast."""
    # Example placeholder logic — replace later with real forecast fetch.
    now = dt_util.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"Forecast fetch simulated at {now}"
    await hass.services.async_call(
        "persistent_notification",
        "create",
        {"title": "HAOS Feature Forecast", "message": msg},
    )


# --- Async wrapper added by integration ---
import asyncio

async def async_fetch_haos_features(hass):
    """Async wrapper to run forecast update logic."""
    try:
        # Import existing sync fetch logic if present
        from . import fetch_haos_features as f
        loop = asyncio.get_running_loop()
        if hasattr(f, "main"):
            await loop.run_in_executor(None, f.main)
        elif hasattr(f, "fetch_haos_features"):
            await loop.run_in_executor(None, f.fetch_haos_features)
        else:
            _LOGGER = __import__("logging").getLogger(__name__)
            _LOGGER.warning("No fetch entrypoint found in fetch_haos_features.py")
    except Exception as err:
        _LOGGER = __import__("logging").getLogger(__name__)
        _LOGGER.warning(f"async_fetch_haos_features failed: {err}")

