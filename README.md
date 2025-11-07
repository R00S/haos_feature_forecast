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

---

## ✨ What's New in v1.4.0

- **HACS Integration Tracking**: Now tracks popular HACS integrations and cards that might be incorporated into Home Assistant
- **Improved Forum Filtering**: Forum feature requests are correctly marked as speculative unless actively being worked on
- **GitHub HACS Discussions**: Monitors discussions about HACS features to identify potential upcoming incorporations
- **Dedicated HACS Section**: Shows 5-10 top HACS features in a separate section
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
  - Popular HACS integrations and Lovelace cards
  - GitHub discussions about HACS features being incorporated
- Rates features by importance (Critical/High/Medium/Low/Minimal) and likelihood (Certain/Very Likely/Likely/Possible/Speculative)
- Sorts features by importance × likelihood
- Intelligently deduplicates similar features from different sources
- Shows popular HACS features in a dedicated section (5-10 features)
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
  - HACS default repositories (popular integrations with 100+ stars, cards with 200+ stars)
  - GitHub discussions about HACS features (hints for potential incorporation)
- Calculates importance based on reactions, comments, views, stars, and labels
- Calculates likelihood based on PR state, milestones, source credibility, activity, and GitHub discussions
- Forum features are marked as speculative since they usually end up in HACS before implementation
- HACS features are tracked separately and shown in their own section
- Deduplicates similar features from different sources, keeping highest-scored version
- Parses current HA version (ignoring patch) to correctly determine upcoming releases
- Stores release data in Home Assistant's data store
- Updates automatically every 6 hours via DataUpdateCoordinator

---

## 📄 License
MIT License © R00S
