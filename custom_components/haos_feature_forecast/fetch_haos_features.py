"""Async-safe forecast fetcher with live GitHub data (HAOS 2025.10 +)."""
# Updated to fetch real release data from GitHub

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Dict, List, Any

import aiohttp

from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

HA_RELEASES = "https://api.github.com/repos/home-assistant/core/releases"
HA_OS_RELEASES = "https://api.github.com/repos/home-assistant/operating-system/releases"

SOURCE_WEIGHTS = {"blog":1.0,"forum":0.9,"reddit":0.8,"github":0.6}
CONF_ORDER = {"Very likely":3,"Likely":2,"Possible":1}

def _src_badge(src, url):
    if url:
        return f'<a href="{url}" target="_blank">{src.title()}</a>'
    return src.title()

def _rank_key(f):
    c = f.get("confidence","Possible"); s = f.get("source","github")
    return (-CONF_ORDER.get(c,1), -SOURCE_WEIGHTS.get(s,0.5))

async def fetch_github_releases(session: aiohttp.ClientSession, url: str) -> List[Dict[str, Any]]:
    """Fetch releases from GitHub API."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                _LOGGER.warning(f"GitHub API returned status {resp.status} for {url}")
                return []
    except Exception as err:
        _LOGGER.error(f"Failed to fetch from {url}: {err}")
        return []

def predict_next_release(releases: List[Dict[str, Any]]) -> datetime:
    """Predict next release date based on historical release cadence."""
    try:
        release_dates = []
        for r in releases[:20]:  # Use last 20 releases
            pub_date = r.get("published_at")
            if pub_date:
                # Parse ISO format with Z timezone
                dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                release_dates.append(dt)
        
        if len(release_dates) < 2:
            # Fallback to monthly cadence
            return datetime.now(timezone.utc) + timedelta(days=30)
        
        release_dates.sort()
        # Calculate average days between releases
        deltas = [(release_dates[i+1] - release_dates[i]).days 
                  for i in range(len(release_dates) - 1)]
        avg_delta = mean(deltas) if deltas else 30
        
        # Predict next release
        next_estimate = release_dates[-1] + timedelta(days=avg_delta)
        return next_estimate
    except Exception as err:
        _LOGGER.warning(f"Error predicting next release: {err}")
        return datetime.now(timezone.utc) + timedelta(days=30)

async def async_fetch_haos_features(hass: HomeAssistant):
    """Forecast with live GitHub release data."""
    try:
        # Fetch live release data from GitHub
        async with aiohttp.ClientSession() as session:
            core_releases, os_releases = await asyncio.gather(
                fetch_github_releases(session, HA_RELEASES),
                fetch_github_releases(session, HA_OS_RELEASES),
            )
        
        # Store the raw data
        release_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "core": [
                {"tag": r["tag_name"], "name": r["name"], "published": r["published_at"]}
                for r in core_releases[:30]
            ],
            "os": [
                {"tag": r["tag_name"], "name": r["name"], "published": r["published_at"]}
                for r in os_releases[:30]
            ],
        }
        
        hass.data.setdefault(DOMAIN, {})["release_data"] = release_data
        
        # Predict next releases
        next_core_date = predict_next_release(core_releases)
        next_os_date = predict_next_release(os_releases)
        
        # Mock features for now (can be enhanced with AI analysis later)
        upcoming = [
            {"title":"Unified Automation Editor","confidence":"Very likely","source":"github","url":"https://github.com/home-assistant/frontend/discussions"},
            {"title":"Energy Dashboard Pie Chart","confidence":"Very likely","source":"blog","url":"https://www.home-assistant.io/blog/"},
            {"title":"Matter 1.3 Support","confidence":"Likely","source":"github","url":"https://github.com/home-assistant/core/discussions"},
            {"title":"Voice Assist Enhancements","confidence":"Likely","source":"forum","url":"https://community.home-assistant.io/c/feature-requests/13"},
            {"title":"Automation Traces UX","confidence":"Possible","source":"github","url":"https://github.com/home-assistant/frontend/discussions"},
            {"title":"Blueprint Debugger","confidence":"Possible","source":"forum","url":"https://community.home-assistant.io/c/blueprints-exchange/53"},
            {"title":"ZHA Diagnostics","confidence":"Possible","source":"github","url":"https://github.com/home-assistant/core/discussions"},
        ]

        nxt = [
            {"title":"Voice Dashboard Presets","confidence":"Likely","source":"reddit","url":"https://www.reddit.com/r/homeassistant/"},
            {"title":"ZHA Stability","confidence":"Possible","source":"github","url":"https://github.com/home-assistant/core/discussions"},
            {"title":"Scene Editor Tweaks","confidence":"Possible","source":"github","url":"https://github.com/home-assistant/frontend/discussions"},
            {"title":"Energy Helpers","confidence":"Possible","source":"forum","url":"https://community.home-assistant.io/c/feature-requests/13"},
        ]

        upcoming = sorted(upcoming, key=_rank_key)[:10]
        nxt = sorted(nxt, key=_rank_key)[:5]

        cet = timezone(timedelta(hours=1))
        ts = datetime.now(cet).strftime("%b %d %H:%M")
        
        # Use predicted release dates - format as Home Assistant versions (e.g., 2025.1 or 2025.12)
        upcoming_ver = f"{next_core_date.year}.{next_core_date.month}"
        next_date = next_core_date + timedelta(days=30)  # Approximate next release
        next_ver = f"{next_date.year}.{next_date.month}"

        def _render(title, items, version, predicted_date):
            lis = ""
            for i in items:
                try:
                    lis += f"<li>{i['title']} <small>— {i.get('confidence','?')} · {_src_badge(i.get('source'), i.get('url'))}</small></li>"
                except Exception as err:
                    _LOGGER.warning(f"Render skip: {err}")
            return f"<h4>{title} ({version}) - Est. {predicted_date.strftime('%b %d')}</h4><ul>{lis}</ul>"

        # Add release statistics
        stats_html = f"<p><small>📊 Last {len(core_releases)} Core releases fetched | Last {len(os_releases)} OS releases fetched</small></p>"
        
        html = (f"<p><b>Last updated:</b> {ts} CET</p>" + 
                stats_html +
                _render("Upcoming", upcoming, upcoming_ver, next_core_date) + 
                _render("Next", nxt, next_ver, next_date))

        hass.data.setdefault(DOMAIN, {})["rendered_html"] = html
        hass.states.async_set("sensor.haos_feature_forecast_native","ok",{"rendered_html": html})
        _LOGGER.info(f"Forecast updated v1.2.0 with live data — {len(core_releases)} core, {len(os_releases)} OS releases")

    except Exception as e:
        _LOGGER.exception("async_fetch_haos_features failed: %s", e)
