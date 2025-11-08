"""Sensor platform for HAOS Feature Forecast (A-rev1 stabilized)."""
from __future__ import annotations
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .coordinator import HaosFeatureForecastCoordinator

_LOGGER = logging.getLogger(__name__)

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
        # Initialize with default state
        self._attr_native_value = "Initializing"
        self._attr_extra_state_attributes = {}

    async def async_update(self) -> None:
        await self.coordinator.async_request_refresh()
        
        # coordinator.data is now a dict with state and attributes
        if isinstance(self.coordinator.data, dict):
            self._attr_native_value = self.coordinator.data.get("state", "Unknown")
            rendered_html = self.coordinator.data.get("rendered_html", "")
            feature_count = self.coordinator.data.get("feature_count", 0)
            
            self._attr_extra_state_attributes = {
                "rendered_html": rendered_html,
                "feature_count": feature_count
            }
            
            # Log diagnostic information for empty card debugging
            if not rendered_html or len(rendered_html) < 100:
                _LOGGER.warning(
                    f"Sensor has minimal/empty HTML content (length: {len(rendered_html)}). "
                    f"Card may appear empty. State: {self._attr_native_value}, "
                    f"Features: {feature_count}. Check logs for rate limiting or fetch errors."
                )
            else:
                _LOGGER.debug(f"Sensor updated: state={self._attr_native_value}, HTML length={len(rendered_html)}, features={feature_count}")
        else:
            # Fallback for old data format (should not happen after update)
            self._attr_native_value = "Ready"
            self._attr_extra_state_attributes = {
                "rendered_html": str(self.coordinator.data),
                "feature_count": 0
            }
            _LOGGER.warning("Sensor received unexpected data format from coordinator")
