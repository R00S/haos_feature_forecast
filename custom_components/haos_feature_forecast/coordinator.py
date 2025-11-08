"""DataUpdateCoordinator for HAOS Feature Forecast."""
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .fetch_haos_features import async_fetch_haos_features

_LOGGER = logging.getLogger(__name__)

class HaosFeatureForecastCoordinator(DataUpdateCoordinator):
    """Coordinator to manage data updates."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=6),
        )
        # Provide helpful initial message instead of empty content
        initial_html = (
            "<p><b>⏳ Initializing HAOS Feature Forecast...</b></p>"
            "<p>First update in progress. This may take 1-2 minutes.</p>"
            "<p><small>If this message persists:</small></p>"
            "<ul>"
            "<li><small>Check logs: <code>ha core logs | grep haos_feature_forecast</code></small></li>"
            "<li><small>Add a GitHub token to avoid rate limits (Settings → Devices & Services → HAOS Feature Forecast → Configure)</small></li>"
            "<li><small>See <a href='https://github.com/R00S/haos_feature_forecast/blob/main/TROUBLESHOOTING.md' target='_blank'>Troubleshooting Guide</a> for more help</small></li>"
            "</ul>"
        )
        self.data = {"state": "Initializing", "rendered_html": initial_html, "feature_count": 0}

    async def _async_update_data(self):
        """Fetch data from the integration."""
        try:
            _LOGGER.info("Coordinator starting data update...")
            await async_fetch_haos_features(self.hass)
            # Return a dict with state and attributes instead of just HTML
            domain_data = self.hass.data.get(DOMAIN, {})
            rendered_html = domain_data.get("rendered_html", "")
            feature_count = domain_data.get("feature_count", 0)
            
            # If we got no data, provide helpful message
            if not rendered_html or rendered_html == "No data":
                _LOGGER.warning("No forecast data available after update - providing helpful error message")
                rendered_html = (
                    "<p><b>⚠️ No forecast data available</b></p>"
                    "<p>The integration couldn't fetch data from GitHub. Common causes:</p>"
                    "<ul>"
                    "<li><b>Rate Limiting:</b> Add a GitHub token (Settings → Devices & Services → Configure)</li>"
                    "<li><b>Network Issues:</b> Check Home Assistant can reach api.github.com</li>"
                    "<li><b>First Run:</b> Wait a few minutes and refresh manually</li>"
                    "</ul>"
                    "<p><small>Check logs: <code>ha core logs | grep haos_feature_forecast</code></small></p>"
                    "<p><small>See <a href='https://github.com/R00S/haos_feature_forecast/blob/main/TROUBLESHOOTING.md' target='_blank'>Troubleshooting Guide</a></small></p>"
                )
                return {
                    "state": "No Data",
                    "rendered_html": rendered_html,
                    "feature_count": 0
                }
            
            _LOGGER.info(f"Coordinator update successful: {feature_count} features, {len(rendered_html)} chars HTML")
            return {
                "state": "OK",
                "rendered_html": rendered_html,
                "feature_count": feature_count
            }
        except Exception as err:
            _LOGGER.error("Error updating HAOS Feature Forecast: %s", err, exc_info=True)
            error_html = (
                "<p><b>❌ Error loading forecast data</b></p>"
                f"<p>Error: {str(err)}</p>"
                "<p><small>Check logs for details: <code>ha core logs | grep haos_feature_forecast</code></small></p>"
                "<p><small>See <a href='https://github.com/R00S/haos_feature_forecast/blob/main/TROUBLESHOOTING.md' target='_blank'>Troubleshooting Guide</a></small></p>"
            )
            return {
                "state": "Error",
                "rendered_html": error_html,
                "feature_count": 0
            }
