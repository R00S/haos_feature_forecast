# Updated 2025-10-30 06:27:51 CET (CET)
"""HAOS Feature Forecast main module."""

import datetime
import aiofiles
import yaml
import os

async def _read_key():
    """Read GitHub token using aiofiles + yaml.safe_load as per your standard."""
    secrets_path = "/config/secrets.yaml"
    if not os.path.exists(secrets_path):
        return None
    async with aiofiles.open(secrets_path, "r") as f:
        data = yaml.safe_load(await f.read())
        return data.get("github_token")

async def get_summary():
    """Return summarized forecast data for sensor.py (stub)."""
    token = await _read_key()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = ("Forecast system ready (GitHub token loaded)" if token
               else "Forecast system ready (no token found)")
    return {
        "summary": summary,
        "timestamp": now,
        "very_likely": ["Energy dashboard enhancements"],
        "likely": ["Voice UI updates"],
        "possible": ["New automation editor preview"],
    }
