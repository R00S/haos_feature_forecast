# Troubleshooting Guide

## Empty Card Issue

If you're seeing an empty card with no errors in the logs, follow these diagnostic steps using the Home Assistant OS Advanced SSH & Terminal.

### 1. Check Integration Status

First, verify that the integration is loaded and configured:

```bash
ha core logs | grep -i "haos_feature_forecast"
```

This shows all log entries related to the integration. Look for:
- `Forecast updated` messages indicating successful updates
- Rate limiting warnings
- GitHub API authentication errors

### 2. Check Sensor State

Verify the sensor exists and has data:

```bash
ha core api --method GET /api/states/sensor.haos_feature_forecast
```

This returns the sensor's state and attributes. Look for:
- `state`: Should be "OK", not "Error" or "Initializing"
- `attributes.rendered_html`: Should contain HTML content, not empty
- `attributes.feature_count`: Should be > 0

### 3. Check for Rate Limiting

GitHub API rate limiting is the most common cause of empty data:

```bash
ha core logs | grep -i "rate limit"
```

If you see rate limit warnings:
1. Go to Settings → Devices & Services → HAOS Feature Forecast → Configure
2. Add a GitHub Personal Access Token (see README for instructions)
3. Without a token: 60 requests/hour
4. With a token: 5000 requests/hour

### 4. Manual Refresh

Force a manual update and watch the logs in real-time:

**Terminal 1 - Watch logs:**
```bash
ha core logs --follow | grep -i "haos_feature_forecast"
```

**Terminal 2 - Trigger update:**
```bash
ha core api --method POST /api/services/haos_feature_forecast/update_forecast
```

Watch Terminal 1 for:
- "Fetched features: X from GitHub..." - indicates successful fetch
- "Forecast updated" - indicates completion
- Any error or warning messages

### 5. Check Home Assistant Logs in Detail

View the full Home Assistant log with timestamps:

```bash
ha core logs --follow
```

Or save to a file for detailed analysis:

```bash
ha core logs > /tmp/ha_logs.txt
grep -i "haos\|forecast\|github" /tmp/ha_logs.txt
```

### 6. Verify Network Connectivity

Test if Home Assistant can reach GitHub:

```bash
curl -I https://api.github.com/repos/home-assistant/core/releases
```

Expected: HTTP 200 response with rate limit headers like:
- `x-ratelimit-limit`: 60 (without token) or 5000 (with token)
- `x-ratelimit-remaining`: Number of requests remaining

### 7. Check Lovelace Card Configuration

Verify your Lovelace card is configured correctly. The card should use:

```yaml
type: markdown
title: Home Assistant Feature Forecast
content: >
  {% set f = state_attr('sensor.haos_feature_forecast','rendered_html') %}
  {{ f if f else "Waiting for forecast data..." }}
```

**Note the sensor entity ID:** `sensor.haos_feature_forecast`

**If you have duplicate sensors** (like `sensor.haos_feature_forecast_2` or `_3`), the integration will automatically remove them on the next restart. This can happen when upgrading from older versions.

To verify in terminal:

```bash
ha core api --method GET /api/states | grep -A 10 haos_feature_forecast
```

If you see multiple entities listed, restart Home Assistant or reload the integration:
```bash
ha core restart
```

After restart, only `sensor.haos_feature_forecast` should remain.

### 8. Check for Cached Data

If the integration isn't fetching new data, check if it has cached data:

```bash
ha core logs | grep -i "using cached data"
```

This indicates the integration is falling back to cached data due to fetch failures.

### 9. Restart Integration

If nothing else works, try restarting the integration:

1. Go to Settings → Devices & Services → HAOS Feature Forecast
2. Click the three dots menu → Reload

Or via terminal:

```bash
ha core restart
```

### 10. Debug Mode

Enable debug logging for more detailed diagnostics:

1. Edit your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.haos_feature_forecast: debug
```

2. Restart Home Assistant:

```bash
ha core restart
```

3. Check logs again:

```bash
ha core logs | grep -i "haos_feature_forecast"
```

## Common Issues and Solutions

### Issue: "No errors but card is empty"

**Cause:** Usually rate limiting or initialization delay

**Solution:**
1. Wait 5-10 minutes after installation for first update
2. Add GitHub token to avoid rate limits
3. Check sensor state (step 2 above)
4. Try manual refresh (step 4 above)

### Issue: "Rate limit exceeded"

**Cause:** GitHub API limits (60/hour without token)

**Solution:**
1. Add GitHub Personal Access Token (see README)
2. Token needs NO special permissions
3. Configure via Settings → Devices & Services → HAOS Feature Forecast → Configure

### Issue: "HACS section is empty or showing 'No confirmed features yet'"

**Cause:** HACS features are filtered by strict criteria - they must have 50+ stars (integrations) or 500+ stars (cards) AND have been updated within the last 3 months

**Solution:**
1. This is normal behavior - the integration only shows popular and actively maintained HACS projects
2. Check logs for HACS filtering statistics:
   ```bash
   ha core logs | grep -i "HACS"
   ```
3. Look for messages like "HACS integrations: checked X, filtered Y, added Z"
4. Without a GitHub token, HACS fetching may be limited by rate limiting
5. Add a GitHub token to ensure full HACS data is fetched
6. The integration only processes the first 10 integrations and 5 cards from HACS to conserve API quota

### Issue: "Multiple sensor entities (sensor.haos_feature_forecast_2, _3, etc.)"

**Cause:** Older versions created duplicate entities during upgrades

**Solution:**
1. The integration now automatically cleans up duplicates on startup
2. Restart Home Assistant or reload the integration:
   ```bash
   ha core restart
   ```
3. Check logs to confirm cleanup:
   ```bash
   ha core logs | grep -i "duplicate\|cleanup"
   ```
4. After cleanup, only `sensor.haos_feature_forecast` should exist
5. Update your Lovelace cards to use `sensor.haos_feature_forecast` if needed

### Issue: "Authentication failed (401)"

**Cause:** Invalid GitHub token

**Solution:**
1. Verify token is still valid in GitHub settings
2. Regenerate token if expired
3. Update token in integration configuration

### Issue: "Sensor not found"

**Cause:** Integration not loaded properly

**Solution:**
1. Verify integration is installed: Settings → Devices & Services
2. Check for configuration errors in logs
3. Reinstall integration via HACS if needed

### Issue: "Waiting for forecast data..."

**Cause:** Integration is running but hasn't completed first update

**Solution:**
1. Wait 5-10 minutes (updates every 6 hours by default)
2. Force manual update (see step 4 above)
3. Check logs for errors during update

## Getting Help

If you've tried all the above steps and still have issues, please open a GitHub issue with:

1. Output of sensor state check (step 2)
2. Relevant log entries (step 5)
3. Rate limit status (step 6)
4. Whether you're using a GitHub token
5. Home Assistant version: `ha core info`

Run this command to collect diagnostic info:

```bash
echo "=== HAOS Feature Forecast Diagnostics ===" > /tmp/diagnostics.txt
echo "" >> /tmp/diagnostics.txt
echo "--- HA Version ---" >> /tmp/diagnostics.txt
ha core info | grep -i version >> /tmp/diagnostics.txt
echo "" >> /tmp/diagnostics.txt
echo "--- Sensor State ---" >> /tmp/diagnostics.txt
ha core api --method GET /api/states/sensor.haos_feature_forecast >> /tmp/diagnostics.txt 2>&1
echo "" >> /tmp/diagnostics.txt
echo "--- Recent Logs ---" >> /tmp/diagnostics.txt
ha core logs | grep -i "haos_feature_forecast" | tail -50 >> /tmp/diagnostics.txt
echo "" >> /tmp/diagnostics.txt
echo "--- Rate Limit Check ---" >> /tmp/diagnostics.txt
curl -I https://api.github.com/repos/home-assistant/core/releases 2>&1 | grep -i rate >> /tmp/diagnostics.txt
echo "" >> /tmp/diagnostics.txt
cat /tmp/diagnostics.txt
```

Copy the output and include it when reporting an issue.
