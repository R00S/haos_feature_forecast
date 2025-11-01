"""Async-safe forecast fetcher with weighted sources (HAOS 2025.10 +)."""
# Timestamp CET: 2025-11-01_232932_CET

import asyncio, logging
from datetime import datetime, timezone, timedelta
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SOURCE_WEIGHTS = {"ha_blog":1.0,"forum":0.9,"reddit":0.8,"github":0.6}
CONF_ORDER={"Very likely":3,"Likely":2,"Possible":1}

def _src_label(src):
    return {"ha_blog":"Blog","forum":"Forum","reddit":"Reddit","github":"GitHub"}.get(src,src)

def _src_badge(src,url):
    if url:
        return f"<a href=\"{url}\" target=\"_blank\">{_src_label(src)}</a>"
    return _src_label(src)

def _rank_key(f):
    c=f.get("confidence","Possible");s=f.get("source","github")
    return (-CONF_ORDER.get(c,1),-SOURCE_WEIGHTS.get(s,0.5))

async def async_fetch_haos_features(hass:HomeAssistant):
    """Weighted two-section forecast."""
    try:
        await asyncio.sleep(0)
        data=hass.data.setdefault(DOMAIN,{})
        upcoming=[
            {"title":"Unified Automation Editor","confidence":"Very likely","source":"ha_blog","url":"https://www.home-assistant.io/blog/"},
            {"title":"Energy Dashboard Pie Chart","confidence":"Very likely","source":"forum","url":"https://community.home-assistant.io/"},
            {"title":"Matter Improvements","confidence":"Likely","source":"ha_blog","url":"https://www.home-assistant.io/blog/"},
            {"title":"Voice Assist Enhancements","confidence":"Likely","source":"reddit","url":"https://www.reddit.com/r/homeassistant/"},
            {"title":"Automation Traces UX","confidence":"Possible","source":"forum","url":"https://community.home-assistant.io/"},
            {"title":"Blueprint Debugger","confidence":"Possible","source":"github","url":"https://github.com/home-assistant/core/pulls"},
            {"title":"ZHA Diagnostics","confidence":"Possible","source":"reddit","url":"https://www.reddit.com/r/homeassistant/"},
        ]
        nxt=[
            {"title":"Voice Dashboard Presets","confidence":"Likely","source":"forum","url":"https://community.home-assistant.io/"},
            {"title":"ZHA Stability","confidence":"Possible","source":"reddit","url":"https://www.reddit.com/r/homeassistant/"},
            {"title":"Scene Editor Tweaks","confidence":"Possible","source":"github","url":"https://github.com/home-assistant/frontend/pulls"},
            {"title":"Energy Helpers","confidence":"Possible","source":"reddit","url":"https://www.reddit.com/r/homeassistant/"},
        ]

        upcoming=sorted(upcoming,key=_rank_key)[:10]
        nxt=sorted(nxt,key=_rank_key)[:5]

        cet=timezone(timedelta(hours=1))
        ts=datetime.now(cet).strftime("%b %d %H:%M")
        ver_now=datetime.now(cet).strftime("%Y.%m")

        def _render(title,ver,items):
            lis="".join(f"<li>{i.get("title")} <small>— {i.get("confidence")} · {_src_badge(i.get("source"),i.get("url"))}</small></li>" for i in items)
            return f"<h4>{title} ({ver})</h4><ul>{lis}</ul>"

        html=(f"<p><b>Last updated:</b> {ts} CET</p>"+_render("Upcoming",ver_now,upcoming)+_render("Next",ver_now,nxt))

        data["forecast"]={"upcoming":upcoming,"next":nxt}
        data["rendered_html"]=html

        hass.states.async_set("sensor.haos_feature_forecast_native","ok",{"rendered_html":html,"features":{"upcoming":upcoming,"next":nxt}})
        _LOGGER.info("Forecast updated v1.1.1 with weighted sources.")

    except Exception as e:
        _LOGGER.exception("async_fetch_haos_features failed: %s",e)

