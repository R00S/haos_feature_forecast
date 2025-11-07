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
        self.data = "Ready"

    async def _async_update_data(self):
        """Fetch data from the integration."""
        try:
            await async_fetch_haos_features(self.hass)
            # Get the rendered HTML from hass.data
            return self.hass.data.get(DOMAIN, {}).get("rendered_html", "No data")
        except Exception as err:
            _LOGGER.error("Error updating HAOS Feature Forecast: %s", err)
            return "Error"
