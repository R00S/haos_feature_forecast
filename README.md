# HAOS Feature Forecast

Forecast upcoming Home Assistant features using AI analysis of public development signals.
This integration automatically gathers recent data from the HA blog, GitHub pull requests, and Reddit to estimate which features are most likely to appear in upcoming Home Assistant OS releases.

---

## 🧩 Installation via HACS

1. In Home Assistant, open **HACS → Integrations → Custom repositories**.
2. Add this repository URL:
   https://github.com/R00S/haos_feature_forecast
   Choose **Integration** as category.
3. Install **HAOS Feature Forecast**.
4. Restart Home Assistant.

---

## ⚙️ Requirements

| Component | Purpose |
|------------|----------|
| **Pyscript** | Executes forecasting logic (`fetch_haos_features.py`) |
| **MQTT broker** | Publishes forecast data |
| **OpenAI API key** | Required for GPT analysis |

Add to `/config/secrets.yaml`:
```yaml
openai_api_key: "sk-yourkey"
```

---

## 🤖 Connecting ChatGPT / OpenAI

The script connects directly to OpenAI using your API key from `secrets.yaml`.

Test connection manually:
```bash
curl -s https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-yourkey"
```
A valid key returns a list of models (e.g. `gpt-4o-mini`).
If connection fails, check Home Assistant → **Settings → System → Logs → Pyscript**.

---

## 📂 Files Installed

| Path | Description |
|------|--------------|
| `custom_components/haos_feature_forecast/` | Minimal sensor shell |
| `pyscript/fetch_haos_features.py` | Full forecasting engine |
| `custom_components/haos_feature_forecast/lovelace_card.yaml` | Markdown card |

---

## 🚀 Run the Forecast

1. Open **Developer Tools → Services**
2. Call:
   ```
   pyscript.fetch_haos_features
   ```
3. Wait 30 s — sensor `sensor.haos_features_native` will appear.

---

## 💡 Lovelace Card

```yaml
type: markdown
title: Home Assistant Feature Forecast
content: >
  {% set f = state_attr('sensor.haos_features_native','rendered_html') %}
  {{ f if f else "Waiting for forecast data..." }}
```

---

## 📊 Output

| Attribute | Meaning |
|------------|----------|
| `state` | Current status |
| `rendered_html` | Full forecast display |
| `upcoming_features` | Predicted for next release |
| `next_features` | Predicted for following release |
| `confidence_overall` | Average confidence score |
| `mqtt_topic` | Publishes JSON to `homeassistant/haos_features/state` |

Data history stored in `/config/pyscript/data/haos_features_history.jsonl`.

---

## 🧠 Notes

- Uses `gpt-4o-mini` with fallback to `gpt-5-mini`
- Manual trigger now, automation later
- Compatible with any Lovelace dashboard

---

## 📄 License
MIT License © R00S
