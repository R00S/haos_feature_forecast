"""Sensor platform for HAOS Feature Forecast (A-rev1 stabilized)."""
from __future__ import annotations
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .coordinator import HaosFeatureForecastCoordinator

async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN]["coordinator"]
    async_add_entities([HaosFeatureForecastSensor(coordinator)], True)

class HaosFeatureForecastSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "HAOS Feature Forecast"
    _attr_unique_id = "haos_feature_forecast_native"
    _attr_icon = "mdi:home-assistant"

    def __init__(self, coordinator: HaosFeatureForecastCoordinator) -> None:
        self.coordinator = coordinator
        self._attr_native_value = coordinator.data

    async def async_update(self) -> None:
        await self.coordinator.async_request_refresh()
        self._attr_native_value = self.coordinator.data
