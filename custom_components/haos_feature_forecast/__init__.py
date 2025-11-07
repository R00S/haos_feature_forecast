from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import Platform
from .const import DOMAIN
from .coordinator import HaosFeatureForecastCoordinator
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Initialize the integration (called before any entry setup)."""
    hass.data.setdefault(DOMAIN, {})

    async def handle_update_forecast(call: ServiceCall):
        """Handle manual forecast update service."""
        try:
            from .fetch_haos_features import async_fetch_haos_features
            asyncio.create_task(async_fetch_haos_features(hass))
            _LOGGER.info("HAOS Feature Forecast: manual update triggered.")
        except Exception as err:
            _LOGGER.warning(f"update_forecast service failed: {err}")

    hass.services.async_register(DOMAIN, "update_forecast", handle_update_forecast)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HAOS Feature Forecast from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create and store the coordinator
    coordinator = HaosFeatureForecastCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN]["coordinator"] = coordinator
    
    # Forward entry setup to platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop("coordinator", None)
    return unload_ok

__version__ = '1.2.0'
