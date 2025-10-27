# Updated 2025-10-28 00:09:10 CET (CET)
"""Fail-safe ConfigFlow for HAOS Feature Forecast (HAOS 2025.10+)."""

from homeassistant import config_entries

DOMAIN = "haos_feature_forecast"

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Minimal working config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the single-step setup."""
        if user_input is not None:
            await self._async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="HAOS Feature Forecast", data={})

        return self.async_show_form(step_id="user")
