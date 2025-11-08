# HAOS Feature Forecast

Forecast upcoming Home Assistant features using live release data from GitHub.
This integration automatically fetches real Home Assistant Core and OS release data from GitHub to predict upcoming releases and features.

---

## 🧩 Installation via HACS

1. In Home Assistant, open **HACS → Integrations → Custom repositories**.
2. Add this repository URL:
   https://github.com/R00S/haos_feature_forecast
   Choose **Integration** as category.
3. Install **HAOS Feature Forecast**.
4. Restart Home Assistant.
5. Go to **Settings → Devices & Services → Add Integration** and search for "HAOS Feature Forecast"
6. **(Optional but Recommended)** Add a GitHub Personal Access Token during setup or later via Integration Options to avoid API rate limiting.

---

## 🔑 GitHub Token Setup (Recommended)

To avoid GitHub API rate limiting (60 requests/hour without token vs 5000 requests/hour with token), it's highly recommended to configure a GitHub Personal Access Token:

### Creating a GitHub Token:
1. Go to GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token** → **Generate new token (classic)**
3. Give it a descriptive name like "Home Assistant HAOS Forecast"
4. **No special scopes/permissions needed** - just leave all checkboxes unchecked (the token only needs to access public data)
5. Click **Generate token** and copy it

### Adding Token to Integration:
- **During initial setup**: Paste the token in the "GitHub Token" field
- **After setup**: Go to **Settings** → **Devices & Services** → **HAOS Feature Forecast** → **Configure** and add/update the token

**Note**: The token is stored securely in Home Assistant and only used to authenticate API requests to GitHub for fetching public repository data.

---

## 🔧 Troubleshooting

If you're experiencing issues like an empty card or no data showing:
- See the **[Troubleshooting Guide](TROUBLESHOOTING.md)** for diagnostic commands and solutions
- Most common issue: GitHub API rate limiting - add a token to fix this
- The guide includes terminal commands for Home Assistant OS Advanced SSH

---

## ✨ What's New in v1.4.0

- **HACS Integration Tracking**: Now tracks popular NEW or recently UPGRADED HACS integrations and cards (within last 3 months)
- **Improved Forum Filtering**: Forum feature requests are correctly marked as speculative unless actively being worked on
- **Dedicated HACS Section**: Shows 3-5 new/updated HACS features in a separate section
- **API Quota Optimization**: Reduced HACS API calls from 300+ to ~15-20 to prevent rate limiting without token
- **Multiple Data Sources**: Fetches actual planned features from GitHub (issues, PRs, discussions), Home Assistant blog, community forums, and HACS
- **Smart Filtering**: Automatically filters out generic maintenance items
- **Importance & Likelihood Ratings**: Each feature is rated and sorted by importance and likelihood
- **Deduplication**: Intelligently merges similar features from different sources
- **Version Bug Fix**: Correctly calculates upcoming/next releases based on current HA version (ignoring patch version)
- **No More Guessing**: Only shows features with real evidence from multiple sources

---

## ⚙️ Features

- Fetches live Home Assistant Core and OS release data from GitHub
- Analyzes real planned features from multiple sources:
  - GitHub issues with new-feature label
  - GitHub pull requests (open feature PRs)
  - GitHub architecture discussions
  - Home Assistant blog posts
  - Community forum feature requests (marked as speculative)
  - Popular NEW or recently UPGRADED HACS integrations and Lovelace cards (last 3 months, limited to conserve API quota)
- Rates features by importance (Critical/High/Medium/Low/Minimal) and likelihood (Certain/Very Likely/Likely/Possible/Speculative)
- Sorts features by importance × likelihood
- Intelligently deduplicates similar features from different sources
- Shows new/updated HACS features in a dedicated section (3-5 features)
- Optimized API usage to work reliably without GitHub token (but token still recommended)
- Correctly determines upcoming and next releases (upcoming = current + 1 month, next = current + 2 months)
- Automatic updates every 6 hours
- Manual update via service call
- Beautiful Lovelace card display

---

## 📂 Files Installed

| Path | Description |
|------|--------------|
| `custom_components/haos_feature_forecast/` | Integration components |
| `custom_components/haos_feature_forecast/lovelace_card.yaml` | Markdown card template |

---

## 🚀 Usage

### Automatic Updates
The integration automatically updates every 6 hours after being configured.

### Manual Update
1. Open **Developer Tools → Services**
2. Call:
   ```
   haos_feature_forecast.update_forecast
   ```
3. Wait a few seconds — sensor will update with latest data.

---

## 💡 Lovelace Card

```yaml
type: markdown
title: Home Assistant Feature Forecast
content: >
  {% set f = state_attr('sensor.haos_feature_forecast_native','rendered_html') %}
  {{ f if f else "Waiting for forecast data..." }}
```

---

## 📊 Output

| Attribute | Meaning |
|------------|----------|
| `state` | Current status |
| `rendered_html` | Full forecast display with live GitHub data |
| `release_data` | Raw release information from GitHub |

---

## 🔧 Technical Details

The integration:
- Fetches up to 30 recent releases from Home Assistant Core and OS repositories
- Analyzes data from multiple sources in parallel:
  - GitHub issues (new-feature label, sorted by reactions)
  - GitHub pull requests (open feature PRs)
  - GitHub architecture discussions
  - Home Assistant blog (RSS feed and web scraping)
  - Community forum (feature requests category via JSON API, marked as speculative)
  - HACS default repositories (NEW or UPGRADED within 3 months: limited to 10 integrations + 5 cards to conserve API quota)
- Optimized to use minimal API calls: works without GitHub token, but token highly recommended for full features
- Tracks recent releases and updates for HACS integrations to show only active development
- Calculates importance based on reactions, comments, views, stars, recency, and labels
- Calculates likelihood based on PR state, milestones, source credibility, and activity
- Forum features are marked as speculative since they usually end up in HACS before implementation
- HACS features are filtered to show only recent activity (new repos or updates within 3 months)
- HACS features are tracked separately and shown in their own "New & Updated HACS Features" section
- Deduplicates similar features from different sources, keeping highest-scored version
- Parses current HA version (ignoring patch) to correctly determine upcoming releases
- Stores release data in Home Assistant's data store
- Updates automatically every 6 hours via DataUpdateCoordinator

---

## 📄 License
MIT License © R00S
