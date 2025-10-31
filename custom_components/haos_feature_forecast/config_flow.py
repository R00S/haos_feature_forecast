from homeassistant import config_entries
from .const import DOMAIN

class HAOSFeatureForecastConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HAOS Feature Forecast."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Initial step for user-triggered flow (no fields)."""
        if user_input is not None:
            return self.async_create_entry(title="HAOS Feature Forecast", data={})
        return self.async_show_form(step_id="user")

