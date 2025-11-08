import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN

class HAOSFeatureForecastConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HAOS Feature Forecast."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Initial step for user-triggered flow."""
        # Check if already configured
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        
        if user_input is not None:
            # Store the GitHub token if provided
            return self.async_create_entry(
                title="HAOS Feature Forecast",
                data={"github_token": user_input.get("github_token", "")}
            )
        
        # Show form with optional GitHub token field
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional("github_token", description={"suggested_value": ""}): str,
            }),
            description_placeholders={
                "github_token": "Optional: GitHub Personal Access Token to avoid rate limiting"
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return HAOSFeatureForecastOptionsFlow(config_entry)


class HAOSFeatureForecastOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for HAOS Feature Forecast."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Update the config entry with new token
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={"github_token": user_input.get("github_token", "")}
            )
            return self.async_create_entry(title="", data={})

        # Pre-fill with existing token
        current_token = self.config_entry.data.get("github_token", "")
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("github_token", description={"suggested_value": current_token}): str,
            })
        )

