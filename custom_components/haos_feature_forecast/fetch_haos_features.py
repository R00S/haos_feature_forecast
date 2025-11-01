"""Thread-safe forecast fetcher for HAOS Feature Forecast."""

import asyncio
import logging
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_fetch_haos_features(hass: HomeAssistant):
    """Fetch upcoming Home Assistant features asynchronously."""
    try:
        await asyncio.sleep(1)
        features = [
            "Energy Pie Chart",
            "Voice Dashboard",
            "New Automation Editor",
            "Improved Matter Support",
        ]

        html = "<h4>Upcoming Home Assistant Features</h4><ul>" + "".join(f"<li>{f}</li>" for f in features) + "</ul>"

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["forecast"] = features
        hass.data[DOMAIN]["rendered_html"] = html

        hass.components.persistent_notification.create(
            "✅ Forecast data simulated and stored successfully.",
            title="HAOS Feature Forecast",
        )
        _LOGGER.info("Forecast updated successfully")

    except Exception as e:
        _LOGGER.exception("async_fetch_haos_features failed: %s", e)
        hass.states.async_set(
            "sensor.haos_feature_forecast_native",
            "Forecast generation failed.",
        )


def main(hass: HomeAssistant):
    """Thread-safe entry point for service handler."""
    try:
        hass.loop.call_soon_threadsafe(
            lambda: asyncio.create_task(async_fetch_haos_features(hass))
        )
    except Exception as e:
        _LOGGER.exception("main() forecast generation failed: %s", e)
        hass.states.async_set(
            "sensor.haos_feature_forecast_native",
            "Forecast generation failed.",
        )
