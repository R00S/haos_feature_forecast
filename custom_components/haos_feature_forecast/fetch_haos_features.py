"""Async-safe forecast fetcher with live GitHub data (HAOS 2025.10 +)."""
# Updated to fetch real feature data from GitHub

import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Dict, List, Any, Optional

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.const import __version__ as HA_VERSION
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

HA_RELEASES = "https://api.github.com/repos/home-assistant/core/releases"
HA_OS_RELEASES = "https://api.github.com/repos/home-assistant/operating-system/releases"
HA_ISSUES = "https://api.github.com/repos/home-assistant/core/issues"

# Importance levels (1-5 scale)
IMPORTANCE_CRITICAL = 5  # Core features, widely used integrations
IMPORTANCE_HIGH = 4      # Popular features, major integrations
IMPORTANCE_MEDIUM = 3    # Moderate impact
IMPORTANCE_LOW = 2       # Minor features, niche integrations
IMPORTANCE_MINIMAL = 1   # Very specific use cases

# Likelihood levels (1-5 scale)
LIKELIHOOD_CERTAIN = 5   # In PR/merged, milestone set
LIKELIHOOD_HIGH = 4      # Active development, clear commitment
LIKELIHOOD_MEDIUM = 3    # Discussed with positive signals
LIKELIHOOD_LOW = 2       # Early discussion, no commitment
LIKELIHOOD_SPECULATIVE = 1  # Just ideas

SOURCE_WEIGHTS = {"pr":1.0,"blog":0.95,"milestone":0.9,"discussion":0.8,"issue":0.7,"forum":0.6}

def parse_ha_version(version_str: str) -> tuple:
    """Parse Home Assistant version string to (year, month).
    
    Examples: '2025.11.1' -> (2025, 11), '2025.1' -> (2025, 1)
    """
    try:
        parts = version_str.split('.')
        return (int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        _LOGGER.warning(f"Could not parse version: {version_str}")
        now = datetime.now()
        return (now.year, now.month)

def get_next_version(year: int, month: int) -> tuple:
    """Get the next version (year, month) after the given version."""
    if month == 12:
        return (year + 1, 1)
    return (year, month + 1)

def _src_badge(src, url):
    if url:
        return f'<a href="{url}" target="_blank">{src.title()}</a>'
    return src.title()

def _importance_label(level: int) -> str:
    """Convert importance level to label."""
    labels = {5: "Critical", 4: "High", 3: "Medium", 2: "Low", 1: "Minimal"}
    return labels.get(level, "Unknown")

def _likelihood_label(level: int) -> str:
    """Convert likelihood level to label."""
    labels = {5: "Certain", 4: "Very likely", 3: "Likely", 2: "Possible", 1: "Speculative"}
    return labels.get(level, "Unknown")

def _rank_key(f):
    """Sort features by importance * likelihood (descending)."""
    importance = f.get("importance", 1)
    likelihood = f.get("likelihood", 1)
    return -(importance * likelihood)

async def fetch_github_data(session: aiohttp.ClientSession, url: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Fetch data from GitHub API."""
    try:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
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

async def fetch_real_features(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """Fetch real planned features from GitHub."""
    features = []
    
    try:
        # Fetch issues and PRs with specific labels indicating planned features
        # Look for issues with milestone, feature-request label, or in-progress PRs
        issues = await fetch_github_data(
            session, 
            HA_ISSUES,
            params={"state": "open", "labels": "new-feature", "per_page": 30, "sort": "reactions-+1"}
        )
        
        for issue in issues[:15]:  # Limit processing
            try:
                # Skip if it's a PR (they have pull_request key)
                if "pull_request" in issue:
                    continue
                
                title = issue.get("title", "")
                # Skip generic or maintenance-related issues
                if any(skip in title.lower() for skip in ["update", "bump", "dependencies", "monthly", "weekly"]):
                    continue
                
                reactions = issue.get("reactions", {}).get("+1", 0)
                comments = issue.get("comments", 0)
                has_milestone = issue.get("milestone") is not None
                labels = [l.get("name", "") for l in issue.get("labels", [])]
                
                # Calculate importance based on reactions and comments
                if reactions > 50 or "core" in labels:
                    importance = IMPORTANCE_CRITICAL
                elif reactions > 20:
                    importance = IMPORTANCE_HIGH
                elif reactions > 10:
                    importance = IMPORTANCE_MEDIUM
                elif reactions > 5:
                    importance = IMPORTANCE_LOW
                else:
                    importance = IMPORTANCE_MINIMAL
                
                # Calculate likelihood based on milestone, labels, and activity
                if has_milestone:
                    likelihood = LIKELIHOOD_HIGH
                elif "in-progress" in labels or comments > 10:
                    likelihood = LIKELIHOOD_MEDIUM
                elif "investigating" in labels:
                    likelihood = LIKELIHOOD_LOW
                else:
                    likelihood = LIKELIHOOD_SPECULATIVE
                
                # Only add features with reasonable importance and likelihood
                if importance >= IMPORTANCE_LOW and likelihood >= LIKELIHOOD_LOW:
                    features.append({
                        "title": title,
                        "importance": importance,
                        "likelihood": likelihood,
                        "source": "issue",
                        "url": issue.get("html_url", "")
                    })
            except Exception as err:
                _LOGGER.debug(f"Error processing issue: {err}")
                continue
        
        # Fetch open PRs that might indicate upcoming features
        prs = await fetch_github_data(
            session,
            "https://api.github.com/repos/home-assistant/core/pulls",
            params={"state": "open", "per_page": 30, "sort": "updated"}
        )
        
        for pr in prs[:15]:
            try:
                title = pr.get("title", "")
                # Skip maintenance PRs
                if any(skip in title.lower() for skip in ["bump", "update dependencies", "translation", "fix typo"]):
                    continue
                
                # Look for feature PRs
                if any(feat in title.lower() for feat in ["add ", "new ", "feature", "implement"]):
                    labels = [l.get("name", "") for l in pr.get("labels", [])]
                    
                    # Calculate importance
                    if "core" in labels or "breaking-change" in labels:
                        importance = IMPORTANCE_HIGH
                    elif "new-integration" in labels:
                        importance = IMPORTANCE_MEDIUM
                    else:
                        importance = IMPORTANCE_LOW
                    
                    # PRs are more certain to land
                    draft = pr.get("draft", False)
                    if draft:
                        likelihood = LIKELIHOOD_MEDIUM
                    else:
                        likelihood = LIKELIHOOD_HIGH
                    
                    if importance >= IMPORTANCE_LOW:
                        features.append({
                            "title": title,
                            "importance": importance,
                            "likelihood": likelihood,
                            "source": "pr",
                            "url": pr.get("html_url", "")
                        })
            except Exception as err:
                _LOGGER.debug(f"Error processing PR: {err}")
                continue
        
    except Exception as err:
        _LOGGER.warning(f"Error fetching real features: {err}")
    
    return features

async def async_fetch_haos_features(hass: HomeAssistant):
    """Forecast with live GitHub release data and real features."""
    try:
        # Get current HA version and parse it (ignoring patch version)
        current_year, current_month = parse_ha_version(HA_VERSION)
        _LOGGER.info(f"Current HA version: {HA_VERSION} -> {current_year}.{current_month}")
        
        # Calculate upcoming and next versions (at least 1 and 2 months ahead)
        upcoming_year, upcoming_month = get_next_version(current_year, current_month)
        next_year, next_month = get_next_version(upcoming_year, upcoming_month)
        
        # Fetch live release data from GitHub
        async with aiohttp.ClientSession() as session:
            core_releases, os_releases, real_features = await asyncio.gather(
                fetch_github_data(session, HA_RELEASES),
                fetch_github_data(session, HA_OS_RELEASES),
                fetch_real_features(session),
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
        
        # Sort features by importance * likelihood
        real_features = sorted(real_features, key=_rank_key)
        
        # Split features between upcoming and next releases
        # Allocate 60% to upcoming, 40% to next
        split_point = max(6, int(len(real_features) * 0.6))
        upcoming = real_features[:min(10, split_point)]
        nxt = real_features[split_point:split_point + 7]
        
        # If we don't have enough real features, skip the release
        # (better to show nothing than show fake data)
        if len(upcoming) < 3:
            _LOGGER.warning("Not enough real features found, showing limited data")
        
        cet = timezone(timedelta(hours=1))
        ts = datetime.now(cet).strftime("%b %d %H:%M")
        
        upcoming_ver = f"{upcoming_year}.{upcoming_month}"
        next_ver = f"{next_year}.{next_month}"

        def _render(title, items, version):
            if not items:
                return f"<h4>{title} ({version})</h4><p><i>No confirmed features yet. Check back later!</i></p>"
            
            lis = ""
            for i in items:
                try:
                    imp_label = _importance_label(i.get('importance', 1))
                    lik_label = _likelihood_label(i.get('likelihood', 1))
                    lis += f"<li>{i['title']} <small>— {imp_label} · {lik_label} · {_src_badge(i.get('source'), i.get('url'))}</small></li>"
                except Exception as err:
                    _LOGGER.warning(f"Render skip: {err}")
            return f"<h4>{title} ({version})</h4><ul>{lis}</ul>"

        # Add release statistics
        stats_html = f"<p><small>📊 Analyzing {len(real_features)} planned features from GitHub</small></p>"
        
        html = (f"<p><b>Last updated:</b> {ts} CET | <b>Current version:</b> {current_year}.{current_month}</p>" + 
                stats_html +
                _render("Upcoming", upcoming, upcoming_ver) + 
                _render("Next", nxt, next_ver))

        hass.data.setdefault(DOMAIN, {})["rendered_html"] = html
        hass.states.async_set("sensor.haos_feature_forecast_native","ok",{"rendered_html": html})
        _LOGGER.info(f"Forecast updated v1.3.0 with {len(real_features)} real features")

    except Exception as e:
        _LOGGER.exception("async_fetch_haos_features failed: %s", e)
