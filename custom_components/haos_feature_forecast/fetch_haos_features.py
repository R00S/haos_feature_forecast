"""Async-safe forecast fetcher for HAOS Feature Forecast (HAOS 2025.10+)."""

import asyncio
import logging
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_fetch_haos_features(hass: HomeAssistant):
    """Fetch upcoming features asynchronously and expose rendered_html."""
    try:
        await asyncio.sleep(0)
        features = [
            "Energy Pie Chart",
            "Voice Dashboard",
            "New Automation Editor",
            "Improved Matter Support",
        ]

        html = ("<h4>Upcoming Home Assistant Features</h4><ul>"
                + "".join(f"<li>{f}</li>" for f in features) + "</ul>")

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["forecast"] = features
        hass.data[DOMAIN]["rendered_html"] = html

        hass.states.async_set(
            "sensor.haos_feature_forecast_native",
            "ok",
            {"rendered_html": html, "features": features},
        )

        await hass.services.async_call(
            "persistent_notification","create",
            {"title": "HAOS Feature Forecast",
             "message": "✅ Forecast simulated & stored."},
        )
        _LOGGER.info("Forecast updated successfully")

    except Exception as e:
        _LOGGER.exception("async_fetch_haos_features failed: %s", e)
        hass.states.async_set(
            "sensor.haos_feature_forecast_native",
            "Forecast generation failed.",
        )
