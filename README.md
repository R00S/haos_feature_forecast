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

## ✨ What's New in v1.3.0

- **Real Feature Data**: Fetches actual planned features from GitHub issues and pull requests
- **Smart Filtering**: Automatically filters out generic maintenance items
- **Importance & Likelihood Ratings**: Each feature is rated and sorted by importance and likelihood
- **Version Bug Fix**: Correctly calculates upcoming/next releases based on current HA version (ignoring patch version)
- **No More Guessing**: Only shows features with real evidence from GitHub sources

---

## ⚙️ Features

- Fetches live Home Assistant Core and OS release data from GitHub
- Analyzes real planned features from GitHub issues and pull requests
- Rates features by importance (Critical/High/Medium/Low/Minimal) and likelihood (Certain/Very Likely/Likely/Possible/Speculative)
- Sorts features by importance × likelihood
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
- Analyzes open GitHub issues with "new-feature" label and open pull requests
- Calculates importance based on reactions, comments, and labels
- Calculates likelihood based on PR state, milestones, and activity
- Parses current HA version (ignoring patch) to correctly determine upcoming releases
- Stores release data in Home Assistant's data store
- Updates automatically every 6 hours via DataUpdateCoordinator

---

## 📄 License
MIT License © R00S
