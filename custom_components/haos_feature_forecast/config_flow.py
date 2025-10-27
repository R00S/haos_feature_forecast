# Updated 2025-10-27 21:37:38 CET (CET)
"""Config flow for HAOS Feature Forecast integration."""

from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN

@config_entries.HANDLERS.register(DOMAIN)
class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for HAOS Feature Forecast."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            await self._async_set_unique_id("haos_feature_forecast_singleton")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="HAOS Feature Forecast", data={})

        return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Required("confirm", default=True): bool}))
