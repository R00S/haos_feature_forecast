"""Async GPT-assisted feature fetcher for HAOS Feature Forecast (HAOS 2025.10+)."""
# Timestamp CET: 2025-11-01_225020_CET

import asyncio
import logging
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

import aiofiles
import yaml
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def _read_key(path: str, key: str) -> str:
    try:
        async with aiofiles.open(path, 'r') as f:
            content = await f.read()
        data = yaml.safe_load(content) or {}
        return data.get(key, '') or ''
    except Exception as e:
        _LOGGER.warning('Failed reading %s from %s: %s', key, path, e)
        return ''

async def _http_get_json(session, url: str, headers: Dict[str, str] | None = None) -> Any:
    try:
        async with session.get(url, headers=headers, timeout=20) as resp:
            if resp.status != 200:
                return None
            return await resp.json()
    except Exception:
        return None

async def _http_get_text(session, url: str, headers: Dict[str, str] | None = None) -> str | None:
    try:
        async with session.get(url, headers=headers, timeout=20) as resp:
            if resp.status != 200:
                return None
            return await resp.text()
    except Exception:
        return None

def _month_version(dt: datetime) -> str:
    # Home Assistant style YYYY.MM
    return f'{dt.year}.{dt.month:02d}'

async def _gather_sources(hass: HomeAssistant) -> List[Dict[str, str]]:
    """Fetch raw items from GitHub, Blog (atom), Forum (Discourse), Reddit JSON, Releases."""
    session = async_get_clientsession(hass)
    headers_json = {'Accept': 'application/vnd.github+json', 'User-Agent': 'haos-feature-forecast/1.1.0'}
    headers_reddit = {'User-Agent': 'haos-feature-forecast/1.1.0'}

    # GitHub PRs (closed/merged recent)
    gh_core = 'https://api.github.com/repos/home-assistant/core/pulls?state=closed&per_page=50'
    gh_rel = 'https://api.github.com/repos/home-assistant/core/releases?per_page=10'

    # HA blog Atom feed (text)
    ha_blog = 'https://www.home-assistant.io/atom.xml'

    # Community forum (Discourse latest)
    forum_latest = 'https://community.home-assistant.io/latest.json'

    # Reddit r/homeassistant
    reddit_new = 'https://www.reddit.com/r/homeassistant/new.json?limit=50'

    gh_core_json, gh_rel_json, blog_text, forum_json, reddit_json = await asyncio.gather(
        _http_get_json(session, gh_core, headers_json),
        _http_get_json(session, gh_rel, headers_json),
        _http_get_text(session, ha_blog),
        _http_get_json(session, forum_latest),
        _http_get_json(session, reddit_new, headers_reddit),
    )

    items: List[Dict[str, str]] = []

    # Parse GitHub PRs
    if isinstance(gh_core_json, list):
        for pr in gh_core_json[:50]:
            title = pr.get('title') or ''
            url = pr.get('html_url') or ''
            if title and url:
                items.append({'title': title, 'url': url, 'source': 'GitHub PR'})

    # Parse GitHub releases
    if isinstance(gh_rel_json, list):
        for rel in gh_rel_json[:10]:
            title = rel.get('name') or rel.get('tag_name') or ''
            url = rel.get('html_url') or ''
            if title and url:
                items.append({'title': title, 'url': url, 'source': 'GitHub Release'})

    # Parse HA blog (very light-weight: take <entry><title> & <link>)
    if blog_text:
        # crude extraction to avoid XML deps
        for chunk in blog_text.split('<entry'):
            if '</entry>' not in chunk:
                continue
            # title
            t0 = chunk.find('<title>'); t1 = chunk.find('</title>')
            title = chunk[t0+7:t1].strip() if (t0!=-1 and t1!=-1) else ''
            # link href
            lu = chunk.find('href=')
            url = ''
            if lu != -1:
                q = chunk[lu:].split('"', 2)
                if len(q) >= 3:
                    url = q[1]
            if title and url:
                items.append({'title': title, 'url': url, 'source': 'HA Blog'})

    # Forum latest topics
    if isinstance(forum_json, dict) and 'topic_list' in forum_json:
        for t in forum_json['topic_list'].get('topics', [])[:30]:
            title = t.get('title') or ''
            tid = t.get('id')
            if title and tid is not None:
                url = f'https://community.home-assistant.io/t/{tid}'
                items.append({'title': title, 'url': url, 'source': 'Forum'})

    # Reddit
    if isinstance(reddit_json, dict):
        for ch in (reddit_json.get('data', {}) or {}).get('children', [])[:30]:
            data = ch.get('data', {})
            title = data.get('title') or ''
            url = data.get('url') or ''
            if title:
                if not url:
                    url = f"https://www.reddit.com{data.get('permalink','')}"
                items.append({'title': title, 'url': url, 'source': 'Reddit'})

    return items

async def _openai_select_features(hass: HomeAssistant, items: List[Dict[str,str]]) -> Dict[str, Any]:
    """Use OpenAI to choose features with confidence and links for Upcoming/Next."""
    # Read key via async pattern
    openai_key = await _read_key('/config/secrets.yaml', 'openai_api_key')
    if not openai_key:
        # fallback to project secrets (dev env)
        openai_key = await _read_key('/home/assistant/secrets.yaml', 'openai_api_key')
    if not openai_key:
        openai_key = await _read_key('/config/.storage/secrets.yaml', 'openai_api_key')

    # If no key, degrade gracefully: map items into a simple selection
    if not openai_key:
        upcoming = items[:8]
        nxt = items[8:12]
        def mk(f):
            return {'name': f['title'], 'confidence': 'Likely', 'url': f['url'], 'source': f['source']}
        return {'upcoming': [mk(x) for x in upcoming], 'next': [mk(x) for x in nxt]}

    session = async_get_clientsession(hass)
    now = datetime.now(timezone(timedelta(hours=1)))
    ver_upcoming = _month_version(now)
    ver_next = _month_version(now.replace(month=now.month+1 if now.month<12 else 1, year=now.year if now.month<12 else now.year+1))

    # Prepare compact corpus for the model
    corpus = []
    for it in items[:80]:
        corpus.append(f"- {it['title']} [src:{it['source']}] ({it['url']})")
    corpus_text = '\n'.join(corpus)

    prompt = (
        'You are assisting with triaging upcoming Home Assistant features.\n'
        f'Produce two JSON arrays: \'upcoming\' (6-10 items for {ver_upcoming}) and \'next\' (3-5 items for {ver_next}).\n'
        'Each item must be an object: {"name","confidence","url","source"}.\n'
        'Confidence ∈ {"Very likely","Likely","Possible"}.\n'
        'Use only items that appear relevant as features; pick strong candidates and include the best source link.\n'
        'Source should be a short label like GitHub PR, GitHub Release, HA Blog, Forum, Reddit.\n\n'
        'Candidates:\n' + corpus_text
    )

    body = {
        'model': 'gpt-4o-mini',
        'messages': [
            {'role': 'system', 'content': 'Respond in JSON only.'},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.2,
        'response_format': {'type': 'json_object'}
    }

    try:
        async with session.post(
            'https://api.openai.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {openai_key}', 'Content-Type': 'application/json'},
            data=json.dumps(body),
            timeout=60
        ) as resp:
            if resp.status != 200:
                _LOGGER.warning('OpenAI non-200: %s', resp.status)
                text = await resp.text()
                _LOGGER.debug('OpenAI body: %s', text)
                # degrade gracefully
                cut = items[:12]
                def mk2(f):
                    return {'name': f['title'], 'confidence': 'Likely', 'url': f['url'], 'source': f['source']}
                return {'upcoming': [mk2(x) for x in cut[:8]], 'next': [mk2(x) for x in cut[8:12]]}
            data = await resp.json()
            content = data['choices'][0]['message']['content']
            return json.loads(content)
    except Exception as e:
        _LOGGER.warning('OpenAI request failed: %s', e)
        # degrade gracefully
        cut = items[:12]
        def mk3(f):
            return {'name': f['title'], 'confidence': 'Likely', 'url': f['url'], 'source': f['source']}
        return {'upcoming': [mk3(x) for x in cut[:8]], 'next': [mk3(x) for x in cut[8:12]]}

def _render_html(ver_upcoming: str, ver_next: str, upcoming: List[Dict[str,str]], nxt: List[Dict[str,str]]) -> str:
    def li(f):
        name = f.get('name','')
        conf = f.get('confidence','')
        url = f.get('url','')
        src = f.get('source','')
        src_html = f'<a href="{url}" target="_blank" rel="noreferrer">{src}</a>' if url else src
        return f'<li><b>{name}</b> <em>({conf})</em><br/><small>{src_html}</small></li>'

    cet = timezone(timedelta(hours=1))
    ts = datetime.now(cet).strftime('%b %d %H:%M')
    up_html = ''.join(li(x) for x in upcoming)
    nx_html = ''.join(li(x) for x in nxt)
    return (
        f"<p><b>Last updated:</b> {ts} CET</p>" 
        f"<h4>Upcoming ({ver_upcoming})</h4><ul>{up_html}</ul>" 
        f"<h4>Next ({ver_next})</h4><ul>{nx_html}</ul>"
    )

async def async_fetch_haos_features(hass: HomeAssistant):
    """Fetch sources, select features via GPT (or degrade), update sensor & data."""
    try:
        items = await _gather_sources(hass)
        selected = await _openai_select_features(hass, items)
        now = datetime.now(timezone(timedelta(hours=1)))
        ver_upcoming = _month_version(now)
        # compute next month safely
        if now.month == 12:
            nxt_dt = now.replace(year=now.year+1, month=1)
        else:
            nxt_dt = now.replace(month=now.month+1)
        ver_next = _month_version(nxt_dt)

        upcoming = selected.get('upcoming', [])[:10]
        nxt = selected.get('next', [])[:5]
        if len(upcoming) < 6 and len(items) > 0:
            fill = [ {'name': it['title'], 'confidence': 'Possible', 'url': it['url'], 'source': it['source']} for it in items if it.get('url') ]
            upcoming = (upcoming + fill)[:6]
        if len(nxt) < 3 and len(items) > 6:
            fill2 = [ {'name': it['title'], 'confidence': 'Possible', 'url': it['url'], 'source': it['source']} for it in items[6:] if it.get('url') ]
            nxt = (nxt + fill2)[:3]

        html = _render_html(ver_upcoming, ver_next, upcoming, nxt)

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]['upcoming'] = upcoming
        hass.data[DOMAIN]['next'] = nxt
        hass.data[DOMAIN]['rendered_html'] = html

        hass.states.async_set(
            'sensor.haos_feature_forecast_native',
            'ok',
            {'rendered_html': html, 'upcoming': upcoming, 'next': nxt},
        )

        await hass.services.async_call(
            'persistent_notification','create',
            {'title': 'HAOS Feature Forecast',
             'message': '✅ Forecast updated from live sources.'},
        )
        _LOGGER.info('Forecast updated successfully with %d sources', len(items))

    except Exception as e:
        _LOGGER.exception('async_fetch_haos_features failed: %s', e)

