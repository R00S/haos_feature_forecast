"""Sensor platform for HAOS Feature Forecast (A-rev1 stabilized)."""
from __future__ import annotations
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN
from .coordinator import HaosFeatureForecastCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN]["coordinator"]
    
    # Check if the sensor entity already exists in the entity registry
    entity_reg = er.async_get(hass)
    unique_id = "haos_feature_forecast"
    
    # Look for existing entity with this unique_id
    existing_entity = entity_reg.async_get_entity_id("sensor", DOMAIN, unique_id)
    
    if existing_entity:
        _LOGGER.info(f"Sensor entity already exists: {existing_entity}, reusing it")
        # Entity already exists, the cleanup in __init__.py should have handled duplicates
        # We still create the sensor object but it will reuse the existing entity
    else:
        _LOGGER.info("Creating new HAOS Feature Forecast sensor")
    
    sensor = HaosFeatureForecastSensor(coordinator)
    async_add_entities([sensor], True)
    _LOGGER.info("HAOS Feature Forecast sensor created and added to Home Assistant")

class HaosFeatureForecastSensor(CoordinatorEntity, SensorEntity):
    """HAOS Feature Forecast sensor using CoordinatorEntity pattern."""
    
    _attr_has_entity_name = False
    _attr_name = "HAOS Feature Forecast"
    _attr_unique_id = "haos_feature_forecast"
    _attr_icon = "mdi:home-assistant"
    
    # Explicitly set the entity_id to prevent duplicates
    entity_id = "sensor.haos_feature_forecast"

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
