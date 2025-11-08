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
        self.data = {"state": "Initializing", "rendered_html": "", "feature_count": 0}

    async def _async_update_data(self):
        """Fetch data from the integration."""
        try:
            await async_fetch_haos_features(self.hass)
            # Return a dict with state and attributes instead of just HTML
            domain_data = self.hass.data.get(DOMAIN, {})
            rendered_html = domain_data.get("rendered_html", "No data")
            feature_count = domain_data.get("feature_count", 0)
            
            return {
                "state": "OK" if rendered_html != "No data" else "No data",
                "rendered_html": rendered_html,
                "feature_count": feature_count
            }
        except Exception as err:
            _LOGGER.error("Error updating HAOS Feature Forecast: %s", err)
            return {"state": "Error", "rendered_html": "Error", "feature_count": 0}
