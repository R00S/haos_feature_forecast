"""Config flow for HAOS Feature Forecast integration."""

from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN


@config_entries.HANDLERS.register(DOMAIN)
class HAOSFeatureForecastFlow(config_entries.ConfigFlow):
    """Handle a config flow for HAOS Feature Forecast."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Initial step."""
        if user_input is not None:
            await self._async_set_unique_id("haos_feature_forecast_singleton")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="HAOS Feature Forecast", data={})

        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))
