# Updated 2025-10-27 21:45:48 CET (CET)
"""Dummy sensor to register the HAOS Feature Forecast integration."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Setup sensor from config entry."""
    async_add_entities([HAOSForecastStatusSensor()])


class HAOSForecastStatusSensor(SensorEntity):
    """Simple sensor showing integration state."""

    _attr_name = "HAOS Feature Forecast"
    _attr_unique_id = "haos_feature_forecast_status"
    _attr_icon = "mdi:cloud-search"

    @property
    def state(self):
        return "active"
