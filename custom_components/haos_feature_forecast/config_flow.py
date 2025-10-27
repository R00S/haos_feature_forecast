"""Config flow for HAOS Feature Forecast integration."""

from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN


class HAOSFeatureForecastFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HAOS Feature Forecast."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            await self._async_set_unique_id("haos_feature_forecast_singleton")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="HAOS Feature Forecast", data={})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={},
        )


async def async_get_options_flow(config_entry):
    """Return the options flow handler."""
    return HAOSFeatureForecastOptionsFlow(config_entry)


class HAOSFeatureForecastOptionsFlow(config_entries.OptionsFlow):
    """Handle options for HAOS Feature Forecast."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=vol.Schema({}))
