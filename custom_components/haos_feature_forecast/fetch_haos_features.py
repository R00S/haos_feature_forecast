
import logging
_LOGGER = logging.getLogger(__name__)

def main(hass=None):
    """Generate HAOS Feature Forecast text."""
    try:
        forecast_text = (
            "🔮 Forecast update simulated.\n"
            "Upcoming features likely to appear in next HA release:\n"
            "• New Energy Dashboard visualizations\n"
            "• Voice Assist improvements\n"
            "• Automation editor overhaul"
        )
        _LOGGER.info("HAOS Feature Forecast simulated successfully.")
        # Send persistent notification if HA context available
        if hass is not None:
            hass.async_create_task(
                hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "HAOS Feature Forecast",
                        "message": forecast_text,
                        "notification_id": "haos_feature_forecast",
                    },
                )
            )
        return forecast_text
    except Exception as err:
        _LOGGER.warning(f"main() forecast generation failed: {err}")
        return "Forecast generation failed."


# --- Async wrapper + helper preserved ---
import asyncio
import inspect
import datetime

async def async_publish_forecast(hass, forecast_text: str):
    """Publish forecast text to HA sensor."""
    try:
        hass.states.async_set(
            "sensor.haos_feature_forecast_native",
            forecast_text or "No forecast data",
            {"last_updated": datetime.datetime.now().isoformat()},
        )
        _LOGGER.info("Forecast sensor updated successfully.")
    except Exception as err:
        _LOGGER.warning(f"Failed to update forecast sensor: {err}")

async def async_fetch_haos_features(hass):
    """Async wrapper to run forecast update logic and publish result."""
    try:
        from . import fetch_haos_features as f
        loop = asyncio.get_running_loop()
        forecast_result = "Forecast update completed."
        if hasattr(f, "main"):
            sig = inspect.signature(f.main)
            if len(sig.parameters) == 0:
                forecast_result = await loop.run_in_executor(None, f.main)
            else:
                forecast_result = await loop.run_in_executor(None, f.main, hass)
        elif hasattr(f, "fetch_haos_features"):
            sig = inspect.signature(f.fetch_haos_features)
            if len(sig.parameters) == 0:
                forecast_result = await loop.run_in_executor(None, f.fetch_haos_features)
            else:
                forecast_result = await loop.run_in_executor(None, f.fetch_haos_features, hass)
        else:
            forecast_result = "No fetch entrypoint found."
            _LOGGER.warning(forecast_result)

        # Always publish forecast state
        await async_publish_forecast(hass, forecast_result)
    except Exception as err:
        _LOGGER.warning(f"async_fetch_haos_features failed: {err}")

