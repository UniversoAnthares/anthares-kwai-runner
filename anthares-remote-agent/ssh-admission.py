"""Conservative private-network budget and public trigger; no agent commands."""
import datetime as dt
import json
import os
import sys
import time
import urllib.parse
import urllib.request

REPO = 'UniversoAnthares/anthares-kwai-runner'
MAX_ATTEMPTS = 120  # 6-minute jobs => at most 720 reserved minutes / 31 days.


def recent_device(data, now):
    try:
        seen = dt.datetime.fromisoformat(data['device_seen_at'].replace('Z', '+00:00'))
        age = (now - seen).total_seconds()
        return (data['service'] == 'anthares-remote-primary'
                and data['state'] == 'neon' and data['device_connected'] is True
                and 0 <= age <= 90)
    except (KeyError, ValueError, TypeError):
        return False


def attempts(runs):
    return sum(max(1, int(run.get('run_attempt', 1))) for run in runs)


def github(path, payload=None):
    request = urllib.request.Request('https://api.github.com/repos/' + REPO + path,
        headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
                 'Accept': 'application/vnd.github+json', 'User-Agent': 'anthares-ssh-recovery'},
        data=None if payload is None else json.dumps(payload).encode(),
        method='GET' if payload is None else 'POST')
    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read()
        return json.loads(body) if body else {}


def budget():
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=31)).isoformat()
    workflow_id = int(github('/actions/runs/' + os.environ.get('GITHUB_RUN_ID', '0'))['workflow_id'])
    used = 0
    for page in range(1, 3):
        query = urllib.parse.urlencode({'created': '>=' + since, 'per_page': 100, 'page': page})
        data = github(f'/actions/workflows/{workflow_id}/runs?' + query)
        used += attempts(data['workflow_runs'])
        if used > MAX_ATTEMPTS:
            raise RuntimeError('SSH quota safety cap reached; no paid fallback or private login')
        if len(data['workflow_runs']) < 100:
            print(f'SSH_BUDGET_ADMITTED={used}/{MAX_ATTEMPTS} reserved_minutes={used * 6}')
            return
    raise RuntimeError('SSH usage history exceeds safe accounting window')


def fresh_heartbeat():
    try:
        with urllib.request.urlopen('https://anthares-remote-primary.vercel.app/health', timeout=10) as response:
            return recent_device(json.load(response), dt.datetime.now(dt.timezone.utc))
    except Exception:
        return False


def monitor():
    if fresh_heartbeat():
        print('SSH_TRIGGER_NOOP=fresh-device-heartbeat; execution-health-not-asserted')
        return
    if os.environ.get('DRY_RUN', 'true') == 'true':
        print('SSH_TRIGGER_DRY_RUN=would-recheck-before-dispatch')
        return
    time.sleep(90)
    if fresh_heartbeat():
        print('SSH_TRIGGER_NOOP=heartbeat-returned-during-grace')
        return
    github('/actions/workflows/anthares-ssh-recovery.yml/dispatches',
           {'ref': 'main', 'inputs': {'mode': 'recover'}})
    print('SSH_RECOVERY_DISPATCHED=1; repair-not-yet-proven')


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('budget', 'monitor'):
        raise SystemExit('expected budget or monitor')
    (budget if sys.argv[1] == 'budget' else monitor)()
