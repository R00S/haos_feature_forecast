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
    
    # Store the config entry for access to GitHub token
    hass.data[DOMAIN]["config_entry"] = entry
    
    # Create and store the coordinator
    coordinator = HaosFeatureForecastCoordinator(hass)
    
    # Perform first refresh - but don't fail if it errors
    # The coordinator will provide a helpful error message in the card
    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info("HAOS Feature Forecast: Initial data fetch completed successfully")
    except Exception as err:
        # Log the error but don't fail setup - coordinator will show error message in card
        _LOGGER.warning(
            f"HAOS Feature Forecast: Initial data fetch failed - {err}. "
            f"The integration will continue to work and retry every 6 hours. "
            f"Check the card for troubleshooting information."
        )
    
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

__version__ = '1.3.0'
