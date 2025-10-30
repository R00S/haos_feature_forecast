# Updated 2025-10-30 06:27:51 CET (CET)
"""Sensor entity for HAOS Feature Forecast."""

from datetime import timedelta
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity, DataUpdateCoordinator, UpdateFailed
)
from .const import DOMAIN
from . import fetch_haos_features

_LOGGER = logging.getLogger(__name__)

class HAOSForecastCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching forecast data."""

    def __init__(self, hass: HomeAssistant):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=6),
        )

    async def _async_update_data(self):
        try:
            data = await fetch_haos_features.get_summary()
            return data
        except Exception as e:
            raise UpdateFailed(f"Feature fetch failed: {e}")

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up HAOS Feature Forecast sensor."""
    coordinator = HAOSForecastCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([HAOSFeatureForecastSensor(coordinator)], update_before_add=True)

class HAOSFeatureForecastSensor(CoordinatorEntity, SensorEntity):
    """Representation of the HAOS Feature Forecast sensor."""

    _attr_name = "HAOS Feature Forecast"
    _attr_unique_id = "haos_feature_forecast_status"
    _attr_icon = "mdi:home-assistant"

    def __init__(self, coordinator: HAOSForecastCoordinator):
        super().__init__(coordinator)
        self._attr_native_value = "loading"

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return "loading"
        if isinstance(data, dict) and "summary" in data:
            return data["summary"]
        return str(data)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if isinstance(data, dict):
            return data
        return {}
