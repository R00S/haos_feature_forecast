from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from .const import DOMAIN
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

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
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True

__version__ = '1.0.3'
