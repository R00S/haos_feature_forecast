"""Init for HAOS Feature Forecast (A-rev1 stabilized)."""
from __future__ import annotations
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.persistent_notification import async_create as pn_create
from .const import DOMAIN
from .coordinator import HaosFeatureForecastCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = HaosFeatureForecastCoordinator(hass)
    hass.data.setdefault(DOMAIN, {})["coordinator"] = coordinator
    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info("HAOS Feature Forecast: initial refresh completed")
    except Exception as e:
        _LOGGER.error("Initial forecast refresh failed: %s", e)
    pn_create(hass, "Forecast integration initialized.", title="HAOS Feature Forecast")

    async def handle_manual_refresh(call: ServiceCall) -> None:
        await coordinator.async_request_refresh()
        pn_create(
            hass,
            f"Manual forecast update completed at {hass.now().strftime('%H:%M:%S')}",
            title="HAOS Feature Forecast",
        )

    hass.services.async_register(DOMAIN, "update_forecast", handle_manual_refresh)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    hass.data.pop(DOMAIN, None)
    hass.services.async_remove(DOMAIN, "update_forecast")
    return True
