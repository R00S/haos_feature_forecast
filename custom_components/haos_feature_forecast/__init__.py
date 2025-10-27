"""HAOS Feature Forecast integration initializer."""

import os
import shutil
from homeassistant.core import HomeAssistant
import homeassistant.util.dt as dt_util

DOMAIN = "haos_feature_forecast"

# Any Pyscript helpers you want distributed
PYSCRIPT_FILES = [
    "fetch_haos_features.py",
    # "parse_reddit_signals.py",
    # "analyze_github_prs.py",
]

async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up the HAOS Feature Forecast integration."""
    await _ensure_pyscript_files(hass)
    return True

async def async_setup(hass: HomeAssistant, config):
    """Legacy YAML setup."""
    await _ensure_pyscript_files(hass)
    return True

async def _ensure_pyscript_files(hass: HomeAssistant):
    """Copy all declared Pyscript files into /config/pyscript."""
    pyscript_dir = os.path.join(hass.config.path(), "pyscript")

    if not os.path.exists(pyscript_dir):
        os.makedirs(pyscript_dir)

    for filename in PYSCRIPT_FILES:
        source = os.path.join(hass.config.path(), "custom_components", DOMAIN, filename)
        dest = os.path.join(pyscript_dir, filename)

        try:
            if not os.path.exists(source):
                hass.components.persistent_notification.create(
                    f"Missing source file: {filename} in {source}",
                    title="HAOS Feature Forecast Error",
                )
                continue

            if (not os.path.exists(dest) or os.path.getmtime(source) > os.path.getmtime(dest)):
                shutil.copy2(source, dest)
                hass.components.persistent_notification.create(
                    f"Copied {filename} to /config/pyscript/ at {dt_util.now().strftime(%Y-%m-%d
%H:%M:%S)}",
                    title="HAOS Feature Forecast",
                )
            else:
                hass.components.persistent_notification.create(
                    f"{filename} already up to date.",
                    title="HAOS Feature Forecast",
                )

        except Exception as e:
            hass.components.persistent_notification.create(
                f"Failed to copy {filename}: {e}",
                title="HAOS Feature Forecast Error",
            )
