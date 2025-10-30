# Updated 2025-10-30 11:50:00 CET (CET)
"""Sensor entity for HAOS Feature Forecast."""

from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor."""
    async_add_entities([HAOSFeatureForecastSensor()])


class HAOSFeatureForecastSensor(SensorEntity):
    """Representation of the HAOS Feature Forecast sensor."""

    _attr_name = "HAOS Feature Forecast"
    _attr_unique_id = "haos_feature_forecast_sensor"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return "Ready"

    @property
    def icon(self):
        """Return an icon for display."""
        return "mdi:home-assistant"
