# Updated 2025-10-27 23:36:22 CET (CET)
"""HAOS Feature Forecast main module."""

import datetime
import aiofiles
import yaml
import os

async def _read_key():
    """Read GitHub token (example of your working method)."""
    secrets_path = "/config/secrets.yaml"
    if not os.path.exists(secrets_path):
        return None
    async with aiofiles.open(secrets_path, "r") as f:
        data = yaml.safe_load(await f.read())
        return data.get("github_token")

async def get_summary():
    """Return summarized forecast data for sensor.py."""
    token = await _read_key()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if token:
        summary = "Forecast system ready (GitHub token loaded)"
    else:
        summary = "Forecast system ready (no token found)"
    return {
        "summary": summary,
        "timestamp": now,
        "very_likely": ["Energy dashboard enhancements"],
        "likely": ["Voice UI updates"],
        "possible": ["New automation editor preview"],
    }
