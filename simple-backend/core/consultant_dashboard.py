"""
Optional consultant-dashboard integration for simple-backend.

This module is additive and fail-open:
- if dashboard config is missing, nothing changes
- if dashboard lookup fails, session startup continues normally
"""

import hashlib
import hmac
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from core.auth import _load_user_profile


def _hash(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _dashboard_enabled(constants):
    return bool(
        constants.get('CONSULTANT_DASHBOARD_URL')
        and constants.get('CONSULTANT_DASHBOARD_INTERNAL_SHARED_SECRET')
    )


def _build_signature_headers(secret, method, path, payload):
    timestamp = str(int(time.time()))
    canonical = f"{timestamp}.{method}.{path}.{payload}".encode('utf-8')
    signature = hmac.new(
        secret.encode('utf-8'),
        canonical,
        hashlib.sha256,
    ).hexdigest()
    return {
        'X-Consultant-Timestamp': timestamp,
        'X-Consultant-Signature': signature,
    }


def _signed_get_json(base_url, path, query_params, shared_secret, timeout_seconds):
    query = urllib.parse.urlencode(query_params)
    headers = _build_signature_headers(shared_secret, 'GET', path, query)
    url = urllib.parse.urljoin(base_url.rstrip('/') + '/', path.lstrip('/'))
    if query:
        url = f"{url}?{query}"
    req = urllib.request.Request(url, headers=headers, method='GET')
    with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))


def _build_identity_query(profile_data):
    query = {}
    google_sub = (profile_data or {}).get('google_sub', '')
    email = ((profile_data or {}).get('email', '') or '').strip().lower()
    if google_sub:
        query['google_sub_hash'] = _hash(google_sub)
    if email:
        query['email_hash'] = _hash(email)
    if profile_data.get('name_hash'):
        query['normalized_name_hash'] = profile_data['name_hash']
    if profile_data.get('phone_hash'):
        query['phone_hash'] = profile_data['phone_hash']
    return query


def build_prompt_addition(client_context):
    if not client_context:
        return ''

    lines = [
        'CONSULTANT DASHBOARD CONTEXT:',
        '- Use this context naturally when helpful, but do not mention a dashboard or internal system.',
        '- Prioritize the current conversation if it conflicts with older context.',
    ]

    notes = (client_context.get('notes') or '').strip()
    if notes:
        lines.append(f"- Background notes: {notes}")

    direction = (client_context.get('direction') or '').strip()
    if direction:
        lines.append(f"- Session direction: {direction}")

    latest_summary = client_context.get('latest_summary') or {}
    if isinstance(latest_summary, dict):
        overview = (latest_summary.get('overview') or latest_summary.get('summary') or '').strip()
        biomarker_summary = (latest_summary.get('biomarker_summary') or '').strip()
        if overview:
            lines.append(f"- Previous session summary: {overview}")
        if biomarker_summary:
            lines.append(f"- Previous biomarker summary: {biomarker_summary}")

    baseline = client_context.get('baseline') or {}
    averages = baseline.get('averages') or {}
    if averages:
        avg_parts = [f"{key}={value}" for key, value in sorted(averages.items())]
        lines.append(f"- Biomarker baseline: {', '.join(avg_parts)}")

    alerts = client_context.get('alerts') or []
    if alerts:
        alert_parts = []
        for alert in alerts[:3]:
            severity = alert.get('severity', 'info')
            title = alert.get('title', 'Alert')
            alert_parts.append(f"{severity}: {title}")
        lines.append(f"- Open alerts: {'; '.join(alert_parts)}")

    return '\n'.join(lines)


def fetch_dashboard_context(constants, user_id_hash):
    if not _dashboard_enabled(constants):
        return None
    if not user_id_hash or user_id_hash == 'anonymous':
        return None

    profile_data = _load_user_profile(constants, user_id_hash)
    if not profile_data:
        print(f"[ConsultantDashboard] No local auth profile for user_id={user_id_hash[:8]}...")
        return None

    query = _build_identity_query(profile_data)
    if not query:
        print(f"[ConsultantDashboard] No identity hashes available for user_id={user_id_hash[:8]}...")
        return None

    base_url = constants['CONSULTANT_DASHBOARD_URL']
    shared_secret = constants['CONSULTANT_DASHBOARD_INTERNAL_SHARED_SECRET']
    timeout_seconds = int(constants.get('CONSULTANT_DASHBOARD_TIMEOUT_SECONDS') or 5)

    try:
        status, resolve_data = _signed_get_json(
            base_url,
            '/internal/resolve-client',
            query,
            shared_secret,
            timeout_seconds,
        )
        if status != 200 or not resolve_data.get('found'):
            print(f"[ConsultantDashboard] resolve-client returned status={status} found={resolve_data.get('found')}")
            return None

        client_id = resolve_data.get('client_id')
        context_status, context_data = _signed_get_json(
            base_url,
            '/internal/client-context',
            {'client_id': client_id},
            shared_secret,
            timeout_seconds,
        )
        if context_status != 200:
            print(f"[ConsultantDashboard] client-context returned status={context_status} client_id={client_id}")
            return None

        result = {
            'client_id': client_id,
            'consultant_id': resolve_data.get('consultant_id') or context_data.get('consultant_id', ''),
            'consultant_name': context_data.get('consultant_name', ''),
            'context': context_data,
            'prompt_addition': build_prompt_addition(context_data),
        }
        print(f"[ConsultantDashboard] Resolved client_id={client_id} consultant_id={result['consultant_id'] or 'none'}")
        return result
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print(f"[ConsultantDashboard] No dashboard client mapping for user_id={user_id_hash[:8]}...")
            return None
        print(f"[ConsultantDashboard] HTTP error: {exc.code} {exc.reason}")
        return None
    except Exception as exc:
        print(f"[ConsultantDashboard] Lookup failed: {exc}")
        return None
