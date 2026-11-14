#!/usr/bin/env python3
"""Read-only retirement audit. Performs no publication or deletion."""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

REPO = 'UniversoAnthares/anthares-kwai-runner'
GH = 'https://api.github.com/repos/' + REPO
NEON = 'https://br-crimson-unit-b89nau08-xledger.compute.c-14.us-east-1.aws.neon.tech/'
NF = 'https://api.northflank.com/v1'

def get(url, token='', timeout=25):
    h = {'Accept':'application/json', 'User-Agent':'Anthares-Northflank-Retirement-Audit/1'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return json.load(r)

def entries(value, name):
    values = (value.get('data') or {}).get(name) or []
    return list(values.values()) if isinstance(values, dict) else values

def proof(comment):
    body = str(comment.get('body') or '')
    if 'X_VIDEO_CONFIRMED_V1' not in body:
        return None
    match = re.search(r'\{[^{}]*"idempotency_key"\s*:\s*"[^"]+"[^{}]*\}', body)
    if not match:
        return None
    data = json.loads(match.group(0))
    key, url = data.get('idempotency_key', ''), data.get('post_url', '')
    if not re.fullmatch(r'[A-Za-z0-9_.:-]{12,160}', key):
        raise ValueError('invalid proof key')
    if not re.fullmatch(r'https://x\.com/lucasyahn/status/[0-9]{8,25}', url):
        raise ValueError('invalid proof URL')
    if data.get('video_verified') is not True:
        raise ValueError('missing video verification')
    return key, url

def main():
    gh = os.environ.get('GH_TOKEN') or ''
    if not gh:
        raise RuntimeError('GH_TOKEN_MISSING')
    flags = {k: os.environ.get(k, '') == '1' for k in (
        'ANTHARES_X_AUTOPUBLISH', 'ANTHARES_X_NEON_LEDGER_VERIFIED',
        'ANTHARES_X_LEGACY_FALLBACK_ARM')}
    query = urllib.parse.urlencode({
        'q': f'repo:{REPO} in:title X-PUBLISH', 'per_page': '100', 'page': '1'})
    issues = get('https://api.github.com/search/issues?' + query, gh)
    all_issues = [x for x in issues.get('items', []) if str(x.get('title', '')).startswith('[X-PUBLISH]')]
    if issues.get('total_count', 0) > 100:
        raise RuntimeError('ISSUE_PAGINATION_REQUIRED')
    receipts, conflicts = {}, []
    for issue in all_issues:
        comments = get(f'{GH}/issues/{issue["number"]}/comments?per_page=100', gh)
        for comment in comments:
            receipt = proof(comment)
            if receipt is None:
                continue
            key, url = receipt
            if key in receipts and receipts[key] != url:
                conflicts.append(issue['number'])
            receipts[key] = url
    health = get(NEON + '?action=health')
    if health.get('ok') is not True:
        raise RuntimeError('NEON_X_LEDGER_HEALTH_FAILED')
    verified = unverified = 0
    for key, url in receipts.items():
        query = urllib.parse.urlencode({'action':'post-status','idempotency_key':key})
        try:
            row = get(NEON + '?' + query, gh)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            unverified += 1
            continue
        if row.get('ok') is True and str(row.get('status', '')).upper() == 'CONFIRMED' and row.get('post_url') == url:
            verified += 1
        else:
            unverified += 1
    token = os.environ.get('NORTHFLANK_API_TOKEN') or ''
    northflank = {'authenticated':False,'services':[], 'ara_log_lines':None,
                  'ara_x_mentions':None,'ara_root_mentions':None}
    if token:
        projects = entries(get(NF + '/projects', token), 'projects')
        project = next((x for x in projects if x.get('name') == 'Default'), None)
        if project:
            pid = project['id']
            services = entries(get(f'{NF}/projects/{pid}/services', token), 'services')
            northflank['authenticated'] = True
            northflank['services'] = [s.get('name') for s in services]
            ara = next((x for x in services if x.get('name') == 'anthares-ara-northflank'), None)
            if ara:
                aid = ara.get('id') or ara['name']
                try:
                    path = f'{NF}/projects/{pid}/services/{aid}/logs?queryType=range&duration=3600&lineLimit=200&direction=backward&type=runtime'
                    logs = get(path, token).get('data') or []
                    if isinstance(logs, dict):
                        logs = list(logs.values())
                    lines = [str(item.get('log') or '') for item in logs if isinstance(item, dict)]
                    northflank['ara_log_lines'] = len(lines)
                    northflank['ara_x_mentions'] = sum(bool(re.search(r'\s/x(?:/|\?|\s)', s)) for s in lines)
                    northflank['ara_root_mentions'] = sum(bool(re.search(r'"(?:GET|POST) /(?!x/)', s)) for s in lines)
                except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
                    pass
    blockers = []
    if not flags['ANTHARES_X_AUTOPUBLISH']:
        blockers.append('GITHUB_X_AUTOPUBLISH_NOT_ARMED')
    if not flags['ANTHARES_X_NEON_LEDGER_VERIFIED']:
        blockers.append('GITHUB_NEON_MIGRATION_FLAG_NOT_SET')
    if flags['ANTHARES_X_LEGACY_FALLBACK_ARM']:
        blockers.append('LEGACY_NORTHFLANK_PUBLISHER_ARMED')
    if unverified or conflicts:
        blockers.append('NEON_VS_GITHUB_RECEIPT_CONFLICT')
    if verified < 9:
        blockers.append('FEWER_THAN_NINE_HISTORICAL_RECEIPTS_VERIFIED')
    if not northflank['authenticated']:
        blockers.append('NORTHFLANK_API_STATUS_UNAVAILABLE')
    blockers.append('ARA_REMOTE_FALLBACK_CUTOVER_NOT_PROVEN')
    result = {
        'mode':'READ_ONLY_NO_PUBLISH_NO_DELETE','github_x_flags':flags,
        'github_issue_total':len(all_issues),
        'github_open_x_issues':[i['number'] for i in all_issues if i.get('state') == 'open'],
        'github_distinct_confirmed_receipts':len(receipts),
        'neon_health_confirmed_count':health.get('confirmed'),
        'neon_receipts_matching_github':verified,
        'neon_receipts_unmatched':unverified,
        'github_receipt_conflicting_issues':conflicts,
        'northflank':northflank,
        'retirement_blockers':blockers,
        'safe_to_delete_ara':False}
    print('ANTHARES_NORTHFLANK_X_RETIREMENT_AUDIT=' + json.dumps(result, sort_keys=True))

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('ANTHARES_NORTHFLANK_AUDIT_ERROR=' + type(exc).__name__)
        sys.exit(2)
