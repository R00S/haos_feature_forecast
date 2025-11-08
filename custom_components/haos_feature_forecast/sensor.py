"""Sensor platform for HAOS Feature Forecast (A-rev1 stabilized)."""
from __future__ import annotations
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .coordinator import HaosFeatureForecastCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN]["coordinator"]
    sensor = HaosFeatureForecastSensor(coordinator)
    async_add_entities([sensor], True)
    _LOGGER.info("HAOS Feature Forecast sensor created and added to Home Assistant")

class HaosFeatureForecastSensor(CoordinatorEntity, SensorEntity):
    """HAOS Feature Forecast sensor using CoordinatorEntity pattern."""
    
    _attr_has_entity_name = True
    _attr_name = "HAOS Feature Forecast"
    _attr_unique_id = "haos_feature_forecast_native"
    _attr_icon = "mdi:home-assistant"

    def __init__(self, coordinator: HaosFeatureForecastCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        _LOGGER.info("HAOS Feature Forecast sensor initializing...")
        
        # Set initial state from coordinator's initial data
        self._update_from_coordinator()
        
        _LOGGER.info(
            f"HAOS Feature Forecast sensor initialized with state: {self._attr_native_value}"
        )

    def _update_from_coordinator(self) -> None:
        """Update sensor state from coordinator data."""
        # coordinator.data is a dict with state and attributes
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
                _LOGGER.info(
                    f"Sensor updated successfully: state={self._attr_native_value}, "
                    f"HTML length={len(rendered_html)}, features={feature_count}"
                )
        else:
            # Fallback for unexpected data format
            self._attr_native_value = "Error"
            self._attr_extra_state_attributes = {
                "rendered_html": (
                    "<p><b>❌ Unexpected data format</b></p>"
                    "<p>The sensor received data in an unexpected format. "
                    "Please check logs and report this issue.</p>"
                ),
                "feature_count": 0
            }
            _LOGGER.error(
                f"Sensor received unexpected data format from coordinator: {type(self.coordinator.data)}"
            )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Always return True so initialization messages are visible
        return True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("Sensor received coordinator update")
        self._update_from_coordinator()
        self.async_write_ha_state()
