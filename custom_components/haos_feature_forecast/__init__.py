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
        _LOGGER.info("="*60)
        _LOGGER.info("HAOS Feature Forecast: Manual update triggered via service call")
        _LOGGER.info("="*60)
        try:
            from .fetch_haos_features import async_fetch_haos_features
            asyncio.create_task(async_fetch_haos_features(hass))
            _LOGGER.info("HAOS Feature Forecast: Manual update task started. Check logs for progress.")
        except Exception as err:
            _LOGGER.error(f"HAOS Feature Forecast: Manual update service failed: {err}", exc_info=True)

    hass.services.async_register(DOMAIN, "update_forecast", handle_update_forecast)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HAOS Feature Forecast from a config entry."""
    _LOGGER.info("="*60)
    _LOGGER.info("HAOS Feature Forecast: Starting integration setup")
    _LOGGER.info("="*60)
    
    hass.data.setdefault(DOMAIN, {})
    
    # Store the config entry for access to GitHub token
    hass.data[DOMAIN]["config_entry"] = entry
    
    # Check if GitHub token is configured
    github_token = entry.data.get("github_token", "").strip()
    if github_token:
        _LOGGER.info("HAOS Feature Forecast: GitHub token configured - using authenticated API access")
    else:
        _LOGGER.warning(
            "HAOS Feature Forecast: No GitHub token configured. "
            "Rate limit: 60 requests/hour. Add a token in integration options to increase to 5000 requests/hour."
        )
    
    # Create and store the coordinator
    _LOGGER.info("HAOS Feature Forecast: Creating coordinator...")
    coordinator = HaosFeatureForecastCoordinator(hass)
    
    # Perform first refresh - but don't fail if it errors
    # The coordinator will provide a helpful error message in the card
    _LOGGER.info("HAOS Feature Forecast: Starting initial data fetch (may take 1-2 minutes)...")
    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info("="*60)
        _LOGGER.info("HAOS Feature Forecast: Initial data fetch completed successfully")
        _LOGGER.info("="*60)
    except Exception as err:
        # Log the error but don't fail setup - coordinator will show error message in card
        _LOGGER.warning("="*60)
        _LOGGER.warning(
            f"HAOS Feature Forecast: Initial data fetch failed - {err}. "
            f"The integration will continue to work and retry every 6 hours. "
            f"Check the card for troubleshooting information."
        )
        _LOGGER.warning("="*60)
    
    hass.data[DOMAIN]["coordinator"] = coordinator
    
    # Forward entry setup to platform
    _LOGGER.info("HAOS Feature Forecast: Setting up sensor platform...")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("HAOS Feature Forecast: Integration setup complete. Check your dashboard card for forecast data.")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop("coordinator", None)
    return unload_ok

__version__ = '1.4.1'
