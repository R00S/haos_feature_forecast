# Updated 2025-10-30 06:27:51 CET (CET)
"""Baseline ConfigFlow verified on HAOS 2025.10."""

from homeassistant import config_entries

DOMAIN = "haos_feature_forecast"

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Minimal config flow for HAOS Feature Forecast."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self._async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="HAOS Feature Forecast", data={})

        return self.async_show_form(step_id="user")
