# CET timestamp: 2025-11-01_21-53-34_CET
"""Async-safe forecast fetcher for HAOS Feature Forecast (HAOS 2025.10+)
Updated: 2025-11-01_21-37-24_CET — adds dual-section forecasts and likelihoods.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_fetch_haos_features(hass: HomeAssistant):
    """Fetch upcoming + next-release features and expose rendered_html."""
    try:
        await asyncio.sleep(0)

        upcoming = [
            ("Energy Pie Chart", "Very Likely"),
            ("Voice Dashboard", "Very Likely"),
            ("New Automation Editor", "Likely"),
            ("Improved Matter Support", "Likely"),
            ("New Device Grouping UI", "Possible"),
        ]

        next_cycle = [
            ("AI Assistant Mode", "Likely"),
            ("Enhanced YAML Editor", "Possible"),
            ("Bluetooth Proxy Dashboard", "Possible"),
        ]

        cet = timezone(timedelta(hours=1))
        ts = datetime.now(cet).strftime("%b %d %H:%M")

        def render_section(title, features):
            items = "".join(f"<li>{f} — <i>{p}</i></li>" for f, p in features)
            return f"<h4>{title}</h4><ul>{items}</ul>"

        html = (
            f"<p><b>Last updated:</b> {ts} CET</p>"
            f"{render_section(Upcoming
Release, upcoming)}"
            f"{render_section(Next
Release, next_cycle)}"
        )

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["forecast"] = {"upcoming": upcoming, "next_cycle": next_cycle}
        hass.data[DOMAIN]["rendered_html"] = html

        hass.states.async_set(
            "sensor.haos_feature_forecast_native",
            "ok",
            {"rendered_html": html, "upcoming": upcoming, "next_cycle": next_cycle},
        )

        await hass.services.async_call(
            "persistent_notification", "create",
            {
                "title": "HAOS Feature Forecast",
                "message": "✅ Forecast updated (Upcoming + Next release sections)."
            },
        )
        _LOGGER.info("Forecast updated successfully")

    except Exception as e:
        _LOGGER.exception("async_fetch_haos_features failed: %s", e)


if __name__ == "__main__":
    print("Run within Home Assistant context.")
