# Updated 2025-10-27 22:59:19 CET (CET)
"""Minimal sensor for HAOS Feature Forecast."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    async_add_entities([HAOSForecastStatusSensor()])

class HAOSForecastStatusSensor(SensorEntity):
    _attr_name = "HAOS Feature Forecast"
    _attr_unique_id = "haos_feature_forecast_status"
    _attr_icon = "mdi:cloud-search"

    @property
    def state(self):
        return "active"
