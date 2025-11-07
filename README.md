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

## ✨ What's New in v1.2.0

- **Live Data Fetching**: Now fetches real release data from GitHub APIs
- **Automatic Predictions**: Calculates next release dates based on historical release cadence
- **Standalone Integration**: No longer requires Pyscript - works as a native Home Assistant integration
- **Improved Visibility**: Integration now appears in the integrations dashboard

---

## ⚙️ Features

- Fetches live Home Assistant Core and OS release data from GitHub
- Predicts next release dates using statistical analysis of historical releases
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
- Calculates average time between releases to predict future releases
- Stores release data in Home Assistant's data store
- Updates automatically every 6 hours via DataUpdateCoordinator

---

## 📄 License
MIT License © R00S
