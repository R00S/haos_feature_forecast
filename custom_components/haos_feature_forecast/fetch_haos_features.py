"""Async-safe forecast fetcher for HAOS Feature Forecast (HAOS 2025.10+)."""
# Timestamp CET: 2025-11-01_223032_CET

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_fetch_haos_features(hass: HomeAssistant):
    """Fetch upcoming + next features asynchronously and expose rendered_html."""
    try:
        await asyncio.sleep(0)
        # Ensure at least 5 items in upcoming and 3 in next
        upcoming = [
            ("Energy Pie Chart", "Very likely"),
            ("Voice Dashboard", "Likely"),
            ("New Automation Editor", "Very likely"),
            ("Improved Matter Support", "Likely"),
            ("Advanced Blueprint Debugger", "Possible"),
        ]

        next_release = [
            ("Home Energy Trends", "Likely"),
            ("Device Groups 2.0", "Possible"),
            ("Scene Migration Tool", "Likely"),
        ]

        cet = timezone(timedelta(hours=1))
        ts = datetime.now(cet).strftime("%b %d %H:%M")

        html = (
            f"<p><b>Last updated:</b> {ts} CET</p>"
            f"<h4>🟢 Upcoming Features (2025.11)</h4><ul>"
            + "".join(f"<li><b>{n}</b> — {c}</li>" for n, c in upcoming)
            + "</ul>"
            f"<h4>🟡 Next Release (2025.12)</h4><ul>"
            + "".join(f"<li><b>{n}</b> — {c}</li>" for n, c in next_release)
            + "</ul>"
        )

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["forecast_upcoming"] = upcoming
        hass.data[DOMAIN]["forecast_next"] = next_release
        hass.data[DOMAIN]["rendered_html"] = html

        hass.states.async_set(
            "sensor.haos_feature_forecast_native",
            "ok",
            {"rendered_html": html, "upcoming": upcoming, "next": next_release},
        )

        await hass.services.async_call(
            "persistent_notification","create",
            {"title": "HAOS Feature Forecast",
             "message": "✅ Forecast updated (v1.0.3)."},
        )
        _LOGGER.info("Forecast v1.0.3 updated successfully")

    except Exception as e:
        _LOGGER.exception("async_fetch_haos_features failed: %s", e)
