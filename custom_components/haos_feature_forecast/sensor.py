"""Dummy sensor to register the HAOS Feature Forecast integration."""

from homeassistant.components.sensor import SensorEntity

async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    """Legacy setup for manual YAML config (unused)."""
    add_entities([HAOSForecastStatusSensor()])

async def async_setup_entry(hass, entry, add_entities):
    """Setup sensor from config entry."""
    add_entities([HAOSForecastStatusSensor()])

class HAOSForecastStatusSensor(SensorEntity):
    """Simple entity showing integration state."""

    _attr_name = "HAOS Feature Forecast"
    _attr_unique_id = "haos_feature_forecast_status"
    _attr_icon = "mdi:cloud-search"

    @property
    def state(self):
        return "active"
