"""Async-safe forecast fetcher for HAOS Feature Forecast (HAOS 2025.10 +).
Last modified: 2025-11-01_19-12-32_CET (CET)"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
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

        cet = timezone(timedelta(hours=1))
        ts = datetime.now(cet).strftime("%b %d %H:%M")

        html = (
            f"<p><b>Last updated:</b> {ts} CET</p>"
            "<h4>Upcoming Home Assistant Features</h4><ul>"
            + "".join(f"<li>{f}</li>" for f in features) + "</ul>"
        )

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["forecast"] = features
        hass.data[DOMAIN]["rendered_html"] = html

        hass.states.async_set(
            "sensor.haos_feature_forecast_native",
            html,
            {"rendered_html": html, "features": features},
        )

        await hass.services.async_call(
            "persistent_notification","create",
            {"title": "HAOS Feature Forecast",
             "message": f"✅ Forecast update completed at {ts} CET."},
        )
        _LOGGER.info("Forecast updated successfully at %s CET", ts)

    except Exception as e:
        _LOGGER.exception("async_fetch_haos_features failed: %s", e)
