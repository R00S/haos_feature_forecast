"""Async-safe forecast fetcher with live data from multiple sources (HAOS 2025.10 +)."""
# Updated to fetch real feature data from GitHub, blog, forums, and other sources

import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Dict, List, Any, Optional
from html.parser import HTMLParser

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.const import __version__ as HA_VERSION
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# GitHub URLs
HA_RELEASES = "https://api.github.com/repos/home-assistant/core/releases"
HA_OS_RELEASES = "https://api.github.com/repos/home-assistant/operating-system/releases"
HA_ISSUES = "https://api.github.com/repos/home-assistant/core/issues"
HA_DISCUSSIONS = "https://api.github.com/repos/home-assistant/architecture/discussions"

# Blog and Forum URLs
HA_BLOG_RSS = "https://www.home-assistant.io/blog/feed.xml"
HA_BLOG = "https://www.home-assistant.io/blog/"
COMMUNITY_FORUM = "https://community.home-assistant.io"

# HACS URLs
HACS_DEFAULT_REPOS = "https://raw.githubusercontent.com/hacs/default/master/data.json"

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

def normalize_title(title: str) -> str:
    """Normalize title for deduplication."""
    # Remove common words and punctuation
    title = title.lower()
    title = re.sub(r'[^\w\s]', '', title)  # Remove punctuation
    # Remove common stop words
    stop_words = {'support', 'feature', 'implementation', 'new', 'add', 'the', 'a', 'an', 'for', 'to', 'of', 'in', 'with'}
    words = [w for w in title.split() if w not in stop_words and len(w) > 2]
    return ' '.join(sorted(words))  # Sort to handle word order

async def fetch_github_data(session: aiohttp.ClientSession, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Fetch data from GitHub API."""
    try:
        async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 200:
                return await resp.json()
            elif resp.status == 403:
                _LOGGER.warning(f"GitHub API rate limit exceeded (status 403). Add a GitHub token in integration options to increase rate limit from 60/hour to 5000/hour.")
                return []
            elif resp.status == 401:
                _LOGGER.error(f"GitHub API authentication failed (status 401). Check that your GitHub token is valid.")
                return []
            else:
                _LOGGER.debug(f"GitHub API returned status {resp.status} for {url}")
                return []
    except Exception as err:
        _LOGGER.debug(f"Failed to fetch from {url}: {err}")
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

async def fetch_real_features(session: aiohttp.ClientSession, headers: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Fetch real planned features from GitHub."""
    features = []
    
    try:
        # Fetch issues and PRs with specific labels indicating planned features
        # Look for issues with milestone, feature-request label, or in-progress PRs
        issues = await fetch_github_data(
            session, 
            HA_ISSUES,
            params={"state": "open", "labels": "new-feature", "per_page": 30, "sort": "reactions-+1"},
            headers=headers
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
            params={"state": "open", "per_page": 30, "sort": "updated"},
            headers=headers
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

async def fetch_blog_features(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """Fetch planned features mentioned in Home Assistant blog posts.
    
    Note: The blog RSS feed may occasionally return 404 due to:
    - DNS/network issues
    - Blog infrastructure changes
    - Rate limiting on the home-assistant.io server
    This is handled gracefully by returning empty list and using cached data.
    """
    features = []
    
    try:
        # Fetch recent blog posts
        async with session.get(HA_BLOG_RSS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                _LOGGER.debug(f"Blog RSS returned status {resp.status} - this is normal if the blog feed is temporarily unavailable")
                return features
            
            content = await resp.text()
            
            # Look for keywords indicating planned features in blog posts
            # Common patterns: "coming soon", "in development", "upcoming", "next release", "working on"
            feature_keywords = [
                r"(?:coming soon|upcoming|in development|working on|next release).*?([A-Z][a-zA-Z\s]{5,50})",
                r"([A-Z][a-zA-Z\s]{5,50}).*?(?:coming soon|upcoming|will be|planned for)",
                r"(?:we're|we are) (?:adding|building|working on|developing) ([A-Z][a-zA-Z\s]{5,50})",
            ]
            
            for pattern in feature_keywords:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in list(matches)[:5]:  # Limit to avoid spam
                    try:
                        feature_text = match.group(1).strip()
                        # Skip if too short or generic
                        if len(feature_text) < 10 or any(skip in feature_text.lower() for skip in ["update", "release", "version"]):
                            continue
                        
                        # Blog mentions are high credibility
                        features.append({
                            "title": feature_text,
                            "importance": IMPORTANCE_HIGH,  # Blog mentions are important
                            "likelihood": LIKELIHOOD_HIGH,   # High likelihood if on blog
                            "source": "blog",
                            "url": HA_BLOG
                        })
                    except Exception as err:
                        _LOGGER.debug(f"Error parsing blog feature: {err}")
                        continue
    
    except Exception as err:
        _LOGGER.warning(f"Error fetching blog features: {err}")
    
    return features

async def fetch_discussion_features(session: aiohttp.ClientSession, headers: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Fetch features from Home Assistant architecture discussions."""
    features = []
    
    try:
        # Fetch GitHub discussions (architecture repo has ADRs and major features)
        discussions = await fetch_github_data(
            session,
            HA_DISCUSSIONS,
            params={"state": "open", "per_page": 20},
            headers=headers
        )
        
        for disc in discussions[:10]:
            try:
                title = disc.get("title", "")
                # Skip if too generic
                if any(skip in title.lower() for skip in ["adr", "question", "meta"]):
                    continue
                
                # Check for "ADR" or "RFC" style discussions (Architecture Decision Records)
                is_adr = "adr" in title.lower() or "rfc" in title.lower()
                comments = disc.get("comments", 0)
                
                # Discussions in architecture repo are important
                if is_adr:
                    importance = IMPORTANCE_HIGH
                    likelihood = LIKELIHOOD_MEDIUM
                elif comments > 5:
                    importance = IMPORTANCE_MEDIUM
                    likelihood = LIKELIHOOD_MEDIUM
                else:
                    importance = IMPORTANCE_LOW
                    likelihood = LIKELIHOOD_LOW
                
                if importance >= IMPORTANCE_LOW:
                    features.append({
                        "title": title,
                        "importance": importance,
                        "likelihood": likelihood,
                        "source": "discussion",
                        "url": disc.get("html_url", "")
                    })
            except Exception as err:
                _LOGGER.debug(f"Error processing discussion: {err}")
                continue
    
    except Exception as err:
        _LOGGER.warning(f"Error fetching discussion features: {err}")
    
    return features

async def fetch_forum_features(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """Fetch popular feature requests from the community forum."""
    features = []
    
    try:
        # Fetch from feature requests category
        # Note: Community forum doesn't have a public API, so we'll use web scraping
        forum_url = f"{COMMUNITY_FORUM}/c/feature-requests/13.json"
        
        async with session.get(forum_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                _LOGGER.debug(f"Could not fetch forum data: {resp.status}")
                return features
            
            data = await resp.json()
            topics = data.get("topic_list", {}).get("topics", [])
            
            for topic in topics[:10]:
                try:
                    title = topic.get("title", "")
                    likes = topic.get("like_count", 0)
                    views = topic.get("views", 0)
                    
                    # Skip meta-posts about the feature request process itself and non-specific topics
                    title_lower = title.lower()
                    
                    # Define skip patterns for meta-posts and non-specific content
                    skip_patterns = [
                        "update", "general", "discussion",  # Original filters
                        "about the", "guidelines", "guide",  # Meta category/process posts
                        "heads-up", "moving",  # Meta announcements
                        "how to", "rules", "process",  # Process documentation
                        "pinned", "sticky",  # Pinned meta-posts
                        "category", "faq", "frequently asked",  # Category information
                        "feature requests are", "feature request guidelines",  # Specific meta-posts about FR process
                    ]
                    
                    # Skip if title matches any skip pattern
                    if any(skip in title_lower for skip in skip_patterns):
                        continue
                    
                    # Skip titles that are too generic or vague (very short titles are often meta)
                    if len(title.strip()) < 15:
                        continue
                    
                    # Calculate importance based on engagement
                    if likes > 50 or views > 1000:
                        importance = IMPORTANCE_HIGH
                    elif likes > 20 or views > 500:
                        importance = IMPORTANCE_MEDIUM
                    elif likes > 10 or views > 200:
                        importance = IMPORTANCE_LOW
                    else:
                        continue  # Skip low engagement
                    
                    # Forum features are speculative unless someone is actively working on them
                    # They usually end up in HACS first before getting implemented
                    likelihood = LIKELIHOOD_SPECULATIVE
                    
                    topic_id = topic.get("id")
                    url = f"{COMMUNITY_FORUM}/t/{topic_id}" if topic_id else COMMUNITY_FORUM
                    
                    features.append({
                        "title": title,
                        "importance": importance,
                        "likelihood": likelihood,
                        "source": "forum",
                        "url": url
                    })
                except Exception as err:
                    _LOGGER.debug(f"Error processing forum topic: {err}")
                    continue
    
    except Exception as err:
        _LOGGER.warning(f"Error fetching forum features: {err}")
    
    return features

async def fetch_hacs_features(session: aiohttp.ClientSession, headers: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Fetch popular NEW or recently UPGRADED HACS integrations and cards."""
    features = []
    
    try:
        _LOGGER.info("Fetching HACS features from default repository...")
        # Fetch HACS default repositories data
        async with session.get(HACS_DEFAULT_REPOS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                _LOGGER.warning(f"Could not fetch HACS data: HTTP {resp.status}")
                return features
            
            data = await resp.json()
            _LOGGER.info(f"HACS data fetched successfully. Found {len(data.get('integrations', []))} integrations and {len(data.get('lovelace', []))} cards")
            
            # Get current time for recency checks
            now = datetime.now(timezone.utc)
            three_months_ago = now - timedelta(days=90)
            
            # Process integrations
            integrations = data.get("integrations", [])
            # Drastically limit iterations to avoid rate limiting - process only 10 integrations
            _LOGGER.info(f"Processing up to 10 HACS integrations (out of {len(integrations)} available)...")
            integrations_checked = 0
            integrations_filtered = 0
            for integration in integrations[:10]:
                try:
                    integrations_checked += 1
                    repo_name = integration.get("repository", "")
                    if not repo_name:
                        continue
                    
                    # Fetch repository details from GitHub to get stars and other metrics
                    repo_url = f"https://api.github.com/repos/{repo_name}"
                    async with session.get(repo_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as repo_resp:
                        if repo_resp.status != 200:
                            continue
                        
                        repo_data = await repo_resp.json()
                        stars = repo_data.get("stargazers_count", 0)
                        description = repo_data.get("description", "")
                        name = repo_data.get("name", "").replace("-", " ").replace("_", " ").title()
                        created_at = repo_data.get("created_at", "")
                        updated_at = repo_data.get("updated_at", "")
                        pushed_at = repo_data.get("pushed_at", "")
                        
                        # Skip if too few stars (not popular enough)
                        if stars < 50:
                            integrations_filtered += 1
                            _LOGGER.debug(f"Filtered {name}: only {stars} stars (need 50+)")
                            continue
                        
                        # Check if it's new or recently updated
                        is_new = False
                        is_updated = False
                        
                        if created_at:
                            created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                            is_new = created_date > three_months_ago
                        
                        if pushed_at:
                            push_date = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                            is_updated = push_date > three_months_ago
                        
                        # Only include if new or recently updated
                        if not (is_new or is_updated):
                            integrations_filtered += 1
                            _LOGGER.debug(f"Filtered {name}: not updated in last 3 months")
                            continue
                        
                        # Skip fetching release info to save API quota
                        # We already know it's recently updated from push_at check
                        recent_release = is_updated
                        release_info = ""
                        
                        # Calculate importance based on stars and recency
                        if is_new and stars > 200:
                            importance = IMPORTANCE_HIGH
                        elif recent_release and stars > 500:
                            importance = IMPORTANCE_HIGH
                        elif stars > 300 or recent_release:
                            importance = IMPORTANCE_MEDIUM
                        elif stars > 100:
                            importance = IMPORTANCE_LOW
                        else:
                            integrations_filtered += 1
                            _LOGGER.debug(f"Filtered {name}: importance too low (stars: {stars})")
                            continue
                        
                        # HACS features are always low likelihood for HA core incorporation
                        # Removed expensive search API call that was consuming API quota
                        likelihood = LIKELIHOOD_LOW
                        
                        # Determine status label
                        status = "New" if is_new else "Updated"
                        
                        # Add to features
                        features.append({
                            "title": f"{name} integration ({status}){release_info}{(' - ' + description[:40]) if description else ''}",
                            "importance": importance,
                            "likelihood": likelihood,
                            "source": "hacs",
                            "url": repo_data.get("html_url", "")
                        })
                        _LOGGER.info(f"Added HACS integration: {name} ({status}, {stars} stars)")
                        
                        # Limit to prevent rate limiting
                        await asyncio.sleep(0.15)
                        
                except Exception as err:
                    _LOGGER.debug(f"Error processing HACS integration: {err}")
                    continue
            
            _LOGGER.info(f"HACS integrations: checked {integrations_checked}, filtered {integrations_filtered}, added {len([f for f in features if 'integration' in f.get('title', '')])}")
            
            # Process lovelace cards
            cards = data.get("lovelace", [])
            # Limit to 5 cards to conserve API quota
            _LOGGER.info(f"Processing up to 5 HACS cards (out of {len(cards)} available)...")
            cards_checked = 0
            cards_filtered = 0
            for card in cards[:5]:
                try:
                    cards_checked += 1
                    repo_name = card.get("repository", "")
                    if not repo_name:
                        continue
                    
                    # Fetch repository details
                    repo_url = f"https://api.github.com/repos/{repo_name}"
                    async with session.get(repo_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as repo_resp:
                        if repo_resp.status != 200:
                            continue
                        
                        repo_data = await repo_resp.json()
                        stars = repo_data.get("stargazers_count", 0)
                        name = repo_data.get("name", "").replace("-", " ").replace("_", " ").title()
                        created_at = repo_data.get("created_at", "")
                        pushed_at = repo_data.get("pushed_at", "")
                        
                        # Skip if too few stars
                        if stars < 100:
                            cards_filtered += 1
                            _LOGGER.debug(f"Filtered card {name}: only {stars} stars (need 100+)")
                            continue
                        
                        # Check if it's new or recently updated
                        is_new = False
                        is_updated = False
                        
                        if created_at:
                            created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                            is_new = created_date > three_months_ago
                        
                        if pushed_at:
                            push_date = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                            is_updated = push_date > three_months_ago
                        
                        # Only include if new or recently updated
                        if not (is_new or is_updated):
                            cards_filtered += 1
                            _LOGGER.debug(f"Filtered card {name}: not updated in last 3 months")
                            continue
                        
                        # Cards need more stars to be considered
                        if stars > 1000:
                            importance = IMPORTANCE_MEDIUM
                        elif stars > 500:
                            importance = IMPORTANCE_LOW
                        else:
                            cards_filtered += 1
                            _LOGGER.debug(f"Filtered card {name}: not enough stars for inclusion (need 500+, has {stars})")
                            continue
                        
                        # Cards are less likely to be incorporated
                        likelihood = LIKELIHOOD_LOW
                        
                        status = "New" if is_new else "Updated"
                        
                        features.append({
                            "title": f"{name} card ({status})",
                            "importance": importance,
                            "likelihood": likelihood,
                            "source": "hacs",
                            "url": repo_data.get("html_url", "")
                        })
                        _LOGGER.info(f"Added HACS card: {name} ({status}, {stars} stars)")
                        
                        await asyncio.sleep(0.15)
                        
                except Exception as err:
                    _LOGGER.debug(f"Error processing HACS card: {err}")
                    continue
            
            _LOGGER.info(f"HACS cards: checked {cards_checked}, filtered {cards_filtered}, added {len([f for f in features if 'card' in f.get('title', '')])}")
            _LOGGER.info(f"Total HACS features collected: {len(features)}")
    
    except Exception as err:
        _LOGGER.warning(f"Error fetching HACS features: {err}")
    
    return features

async def async_fetch_haos_features(hass: HomeAssistant):
    """Forecast with live data from multiple sources."""
    _LOGGER.info("Starting forecast data fetch from multiple sources...")
    try:
        # Get current HA version and parse it (ignoring patch version)
        current_year, current_month = parse_ha_version(HA_VERSION)
        _LOGGER.info(f"Current HA version: {HA_VERSION} -> {current_year}.{current_month}")
        
        # Calculate upcoming and next versions (at least 1 and 2 months ahead)
        upcoming_year, upcoming_month = get_next_version(current_year, current_month)
        next_year, next_month = get_next_version(upcoming_year, upcoming_month)
        
        # Initialize domain data if not present
        hass.data.setdefault(DOMAIN, {})
        
        # Get cached data as fallback
        cached_data = hass.data[DOMAIN].get("cached_features", {})
        
        # Get GitHub token from config entry if available
        github_token = None
        config_entry = hass.data[DOMAIN].get("config_entry")
        if config_entry:
            github_token = config_entry.data.get("github_token", "").strip()
        
        # Prepare headers for GitHub API requests
        headers = {}
        if github_token:
            headers["Authorization"] = f"token {github_token}"
            _LOGGER.debug("Using GitHub token for API requests")
        else:
            _LOGGER.warning("No GitHub token configured - API rate limits will be restrictive (60 requests/hour). Add a token in integration options to increase limit to 5000 requests/hour.")
        
        # Fetch data from multiple sources in parallel
        async with aiohttp.ClientSession() as session:
            results = await asyncio.gather(
                fetch_github_data(session, HA_RELEASES, headers=headers),
                fetch_github_data(session, HA_OS_RELEASES, headers=headers),
                fetch_real_features(session, headers=headers),
                fetch_blog_features(session),
                fetch_discussion_features(session, headers=headers),
                fetch_forum_features(session),
                fetch_hacs_features(session, headers=headers),
                return_exceptions=True  # Don't fail if one source fails
            )
            
            # Use cached data as fallback if fetch fails or returns empty
            core_releases = results[0] if not isinstance(results[0], Exception) and results[0] else cached_data.get("core_releases", [])
            os_releases = results[1] if not isinstance(results[1], Exception) and results[1] else cached_data.get("os_releases", [])
            github_features = results[2] if not isinstance(results[2], Exception) and results[2] else cached_data.get("github_features", [])
            blog_features = results[3] if not isinstance(results[3], Exception) and results[3] else cached_data.get("blog_features", [])
            discussion_features = results[4] if not isinstance(results[4], Exception) and results[4] else cached_data.get("discussion_features", [])
            forum_features = results[5] if not isinstance(results[5], Exception) and results[5] else cached_data.get("forum_features", [])
            hacs_features = results[6] if not isinstance(results[6], Exception) and results[6] else cached_data.get("hacs_features", [])
        
        # Log which sources failed and are using cache
        if isinstance(results[2], Exception) or not results[2]:
            _LOGGER.info(f"GitHub features fetch returned no data, using cached data ({len(github_features)} features). This may be due to rate limiting - consider adding a GitHub token.")
        if isinstance(results[3], Exception) or not results[3]:
            _LOGGER.debug(f"Blog features fetch returned no data, using cached data ({len(blog_features)} features). The blog RSS feed may be temporarily unavailable.")
        if isinstance(results[4], Exception) or not results[4]:
            _LOGGER.debug(f"Discussion features fetch returned no data, using cached data ({len(discussion_features)} features)")
        if isinstance(results[5], Exception) or not results[5]:
            _LOGGER.debug(f"Forum features fetch returned no data, using cached data ({len(forum_features)} features)")
        if isinstance(results[6], Exception) or not results[6]:
            _LOGGER.info(f"HACS features fetch returned no data, using cached data ({len(hacs_features)} features). This may be due to rate limiting - consider adding a GitHub token.")
        
        # Cache successful fetches for future fallback
        hass.data[DOMAIN]["cached_features"] = {
            "core_releases": core_releases if core_releases else cached_data.get("core_releases", []),
            "os_releases": os_releases if os_releases else cached_data.get("os_releases", []),
            "github_features": github_features if github_features else cached_data.get("github_features", []),
            "blog_features": blog_features if blog_features else cached_data.get("blog_features", []),
            "discussion_features": discussion_features if discussion_features else cached_data.get("discussion_features", []),
            "forum_features": forum_features if forum_features else cached_data.get("forum_features", []),
            "hacs_features": hacs_features if hacs_features else cached_data.get("hacs_features", []),
        }
        
        # Combine all features from different sources (HACS is kept separate for its own section)
        all_features = github_features + blog_features + discussion_features + forum_features
        
        _LOGGER.info(f"Fetched features: {len(github_features)} from GitHub, "
                    f"{len(blog_features)} from blog, {len(discussion_features)} from discussions, "
                    f"{len(forum_features)} from forum, {len(hacs_features)} from HACS")
        
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
        
        # Deduplicate features by normalized title, keeping the highest scored one
        seen_normalized = {}
        unique_features = []
        
        for f in all_features:
            normalized = normalize_title(f["title"])
            
            if not normalized:  # Skip if normalization resulted in empty string
                continue
            
            if normalized in seen_normalized:
                # Keep the feature with higher importance * likelihood
                existing = seen_normalized[normalized]
                existing_score = existing['importance'] * existing['likelihood']
                new_score = f['importance'] * f['likelihood']
                
                if new_score > existing_score:
                    # Replace with better feature
                    unique_features.remove(existing)
                    seen_normalized[normalized] = f
                    unique_features.append(f)
                    _LOGGER.debug(f"Replaced duplicate: '{existing['title']}' with '{f['title']}'")
            else:
                seen_normalized[normalized] = f
                unique_features.append(f)
        
        # Sort features by importance * likelihood
        unique_features = sorted(unique_features, key=_rank_key)
        
        # Process HACS features separately - they deserve their own section
        hacs_features_sorted = sorted(hacs_features, key=_rank_key)
        top_hacs = hacs_features_sorted[:5]  # Show top 3-5 HACS features (reduced to conserve display space)
        
        # Log HACS features for debugging
        if not hacs_features:
            _LOGGER.warning("No HACS features found. This could be due to: 1) Rate limiting, 2) No features match criteria (50+ stars, updated within 3 months), 3) HACS data fetch failed")
        else:
            _LOGGER.info(f"Found {len(hacs_features)} HACS features, showing top {len(top_hacs)}")
            if _LOGGER.isEnabledFor(logging.DEBUG):
                for idx, feat in enumerate(top_hacs, 1):
                    _LOGGER.debug(f"  HACS {idx}: {feat.get('title', 'Unknown')}")
        
        # Split features between upcoming and next releases
        # Allocate 60% to upcoming, 40% to next
        split_point = max(6, int(len(unique_features) * 0.6))
        upcoming = unique_features[:min(10, split_point)]
        nxt = unique_features[split_point:split_point + 7]
        
        # If we don't have enough real features, show warning
        if len(upcoming) < 3:
            _LOGGER.warning("Not enough real features found, showing limited data. This may result in an empty or minimal card display.")
        
        # Log total feature count for diagnostics
        _LOGGER.info(f"Processing {len(unique_features)} unique features and {len(top_hacs)} HACS features for display")
        
        cet = timezone(timedelta(hours=1))
        ts = datetime.now(cet).strftime("%b %d %H:%M")
        
        upcoming_ver = f"{upcoming_year}.{upcoming_month}"
        next_ver = f"{next_year}.{next_month}"

        def _render(title, items, version=None):
            version_text = f" ({version})" if version else ""
            if not items:
                return f"<h4>{title}{version_text}</h4><p><i>No confirmed features yet. Check back later!</i></p>"
            
            lis = ""
            for i in items:
                try:
                    imp_label = _importance_label(i.get('importance', 1))
                    lik_label = _likelihood_label(i.get('likelihood', 1))
                    lis += f"<li>{i['title']} <small>— {imp_label} · {lik_label} · {_src_badge(i.get('source'), i.get('url'))}</small></li>"
                except Exception as err:
                    _LOGGER.warning(f"Render skip: {err}")
            return f"<h4>{title}{version_text}</h4><ul>{lis}</ul>"

        # Add release statistics with sources breakdown (including HACS)
        source_counts = {}
        for f in all_features:
            src = f.get('source', 'unknown')
            source_counts[src] = source_counts.get(src, 0) + 1
        if hacs_features:
            source_counts['hacs'] = len(hacs_features)
        
        source_text = ", ".join([f"{count} from {src}" for src, count in source_counts.items()])
        stats_html = f"<p><small>📊 Analyzing {len(unique_features)} unique features ({source_text})</small></p>"
        
        html = (f"<p><b>Last updated:</b> {ts} CET | <b>Current version:</b> {current_year}.{current_month}</p>" + 
                stats_html +
                _render("Upcoming", upcoming, upcoming_ver) + 
                _render("Next", nxt, next_ver) +
                _render("New & Updated HACS Features", top_hacs))

        hass.data.setdefault(DOMAIN, {})["rendered_html"] = html
        hass.data[DOMAIN]["feature_count"] = len(unique_features)
        # Also cache the last successful HTML render
        hass.data[DOMAIN]["last_successful_html"] = html
        hass.data[DOMAIN]["last_successful_count"] = len(unique_features)
        
        # Log HTML length for diagnostics
        _LOGGER.info(f"Generated forecast HTML ({len(html)} characters) with {len(unique_features)} features and {len(top_hacs)} HACS features")
        
        # Warn if HTML is suspiciously short (likely empty/error)
        if len(html) < 200:
            _LOGGER.warning(f"Generated HTML is very short ({len(html)} chars) - card may appear empty. Check if data sources are accessible.")
        
        # Note: We no longer set state directly here, the coordinator/sensor handles it
        _LOGGER.info(f"Forecast updated v1.4.3 with {len(unique_features)} real features from multiple sources and {len(top_hacs)} HACS features")

    except Exception as e:
        _LOGGER.exception("async_fetch_haos_features failed: %s", e)
        # On complete failure, try to use last successful HTML if available
        hass.data.setdefault(DOMAIN, {})
        last_html = hass.data[DOMAIN].get("last_successful_html")
        last_count = hass.data[DOMAIN].get("last_successful_count", 0)
        if last_html:
            _LOGGER.warning("Using last successful cached HTML due to fetch failure")
            hass.data[DOMAIN]["rendered_html"] = last_html
            hass.data[DOMAIN]["feature_count"] = last_count
        else:
            _LOGGER.error("No cached data available, forecast unavailable")
            hass.data[DOMAIN]["rendered_html"] = "Error: No data available"
            hass.data[DOMAIN]["feature_count"] = 0
