# Copilot Instructions for HAOS Feature Forecast

## Project Overview

HAOS Feature Forecast is a Home Assistant custom integration that forecasts upcoming Home Assistant features by fetching live release data from GitHub, the Home Assistant blog, community forums, and HACS (Home Assistant Community Store).

**Key Characteristics:**
- **Type**: Home Assistant custom integration
- **Language**: Python (async/await patterns)
- **Integration Type**: Service integration with cloud polling
- **Minimum HA Version**: 2024.1.0
- **Quality Scale**: Silver
- **Distribution**: HACS (Home Assistant Community Store)

## Architecture

### Component Structure

```
custom_components/haos_feature_forecast/
├── __init__.py          # Entry point, service registration, entity cleanup
├── manifest.json        # Integration metadata
├── const.py            # Constants (DOMAIN)
├── coordinator.py      # DataUpdateCoordinator (6-hour update cycle)
├── sensor.py           # Sensor entity definition
├── config_flow.py      # Configuration UI flow (GitHub token setup)
├── fetch_haos_features.py  # Core logic: fetch & analyze features
├── services.yaml       # Service definitions
├── strings.json        # UI strings
└── translations/       # Localized strings
```

### Data Flow

1. **Coordinator** (`coordinator.py`) triggers updates every 6 hours
2. **Fetcher** (`fetch_haos_features.py`) queries multiple sources in parallel:
   - GitHub API (releases, issues, PRs, discussions)
   - Home Assistant blog (RSS + web scraping)
   - Community forum (JSON API)
   - HACS default repositories
3. **Data Processing**: Features are scored, deduplicated, and formatted as HTML
4. **Sensor** (`sensor.py`) exposes data via `rendered_html` attribute
5. **Display**: Lovelace markdown card renders the forecast

## Code Style & Conventions

### Python Style
- Follow Home Assistant development guidelines
- Use async/await for all I/O operations
- Type hints for function signatures (where applicable)
- Docstrings for classes and complex functions
- Use `_LOGGER` for logging (already imported in each module)

### Logging Conventions
```python
import logging
_LOGGER = logging.getLogger(__name__)

# Use appropriate log levels:
_LOGGER.debug("Detailed debug information")
_LOGGER.info("Important state changes or progress")
_LOGGER.warning("Recoverable issues")
_LOGGER.error("Errors with context", exc_info=True)
```

### Naming Conventions
- Constants: `UPPER_SNAKE_CASE` (e.g., `DOMAIN`, `HA_RELEASES`)
- Functions: `snake_case` (async functions prefixed with `async_`)
- Classes: `PascalCase` (e.g., `HaosFeatureForecastCoordinator`)
- Private functions: `_leading_underscore`

### Home Assistant Patterns
- Use `DataUpdateCoordinator` for periodic updates
- ConfigEntry-based setup (no YAML configuration)
- Store data in `hass.data[DOMAIN]`
- Use `aiohttp` for HTTP requests
- Handle rate limiting gracefully (especially GitHub API)

## Key Dependencies

- **aiohttp**: Async HTTP client for API requests
- **Home Assistant Core**: Platform and helper utilities
- **No external dependencies** beyond aiohttp (by design for HACS compatibility)

## Development Guidelines

### Making Changes

1. **Minimal Changes**: This is a production integration used by real users
   - Make surgical, focused changes
   - Preserve backward compatibility
   - Don't break existing functionality

2. **Testing Considerations**:
   - No formal test suite exists (typical for HACS integrations)
   - Manual testing in Home Assistant environment required
   - Test with and without GitHub token (rate limiting scenarios)
   - Verify sensor state and attributes in Developer Tools

3. **API Rate Limiting**:
   - Always respect GitHub API rate limits
   - Code should work without authentication (60 req/hour)
   - Token usage increases limit to 5000 req/hour
   - HACS queries are minimized (~15-20 calls) to conserve quota

### Common Tasks

#### Adding New Data Sources
- Add URL constant at top of `fetch_haos_features.py`
- Create async fetch function with error handling
- Add to parallel fetch in `async_fetch_haos_features()`
- Apply scoring logic (importance × likelihood)
- Test rate limiting behavior

#### Modifying Scoring Logic
- Importance levels: 1-5 (IMPORTANCE_MINIMAL to IMPORTANCE_CRITICAL)
- Likelihood levels: 1-5 (LIKELIHOOD_SPECULATIVE to LIKELIHOOD_CERTAIN)
- Source weights defined in `SOURCE_WEIGHTS` dict
- Features sorted by `importance * likelihood * source_weight`

#### Changing Update Frequency
- Modify `update_interval` in `coordinator.py` (currently 6 hours)
- Consider impact on API rate limits
- Balance freshness vs. resource usage

### Configuration & Setup

#### GitHub Token (Optional but Recommended)
- Configured via ConfigFlow (`config_flow.py`)
- Stored securely in Home Assistant
- Accessed via entry options: `entry.options.get("github_token")`
- No special permissions needed (public read-only access)

#### Manual Update Service
- Service: `haos_feature_forecast.update_forecast`
- Defined in `__init__.py` via `async_setup()`
- Triggers immediate data fetch outside update cycle

## Important Notes

### Version Handling
- Current HA version parsed from `homeassistant.const.__version__`
- Patch version ignored (e.g., `2025.11.3` → `2025.11`)
- Upcoming release = current + 1 month
- Next release = current + 2 months

### Entity Cleanup
- Integration automatically removes duplicate entities on upgrade
- Correct entity_id: `sensor.haos_feature_forecast`
- Correct unique_id: `haos_feature_forecast`
- Cleanup logic in `__init__.py`: `_cleanup_old_entities()`

### HTML Generation
- Output stored in `hass.data[DOMAIN]["rendered_html"]`
- Must be valid HTML (used in markdown card)
- Include helpful error messages when data unavailable
- Link to troubleshooting guide on errors

### HACS Considerations
- Only show NEW or UPDATED integrations/cards (last 3 months)
- Separate section for HACS features (don't mix with HA features)
- Limited to 10 integrations + 5 cards (API quota conservation)
- Filter out inactive or unmaintained repositories

## Troubleshooting

### Common Issues
1. **Empty card/no data**: Usually GitHub rate limiting → add token
2. **Stale data**: Check coordinator logs, verify 6-hour update cycle
3. **Missing HACS features**: Check filtering logic (3-month window, repository activity)
4. **Duplicate entities**: Should auto-cleanup on upgrade, check logs

### Debug Commands (Home Assistant OS)
```bash
# View logs
ha core logs | grep haos_feature_forecast

# Check sensor state
ha states | grep haos_feature_forecast

# Restart Home Assistant
ha core restart
```

## File Modification Guidelines

### When editing `fetch_haos_features.py`:
- This is the core logic file (~1000+ lines)
- Preserve parallel async fetch pattern
- Maintain error handling for each data source
- Test rate limiting scenarios

### When editing `coordinator.py`:
- Keep update interval reasonable (consider API limits)
- Preserve helpful initialization message
- Maintain error recovery logic

### When editing `__init__.py`:
- Don't remove entity cleanup logic
- Preserve service registration
- Maintain domain data initialization

### When editing `config_flow.py`:
- Keep GitHub token validation logic
- Preserve options flow for token updates
- Maintain backward compatibility

## Release Process

1. Update version in `manifest.json`
2. Update README.md with changelog
3. Test installation via HACS
4. Verify upgrade path from previous version
5. Check entity cleanup works correctly
6. Tag release in GitHub

---

**For Contributors**: This integration prioritizes reliability and API quota efficiency. Always test changes with and without GitHub token, and consider the impact on rate limiting. When in doubt, preserve existing behavior.
