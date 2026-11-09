#!/usr/bin/env python3
"""CF-12/CF-13: GitHub-hosted Cloudflare Free plan quota guard.

External scheduled monitor. No Cloudflare Cron/DO/KV/Queue resources.
Issue body holds a small control-state ledger for reversible actions.
No media, agent, essential controller, billing or plan mutations.
"""
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

ACCOUNT = "5c24be052e5144391f73a8e03491e88e"
REPO = "UniversoAnthares/anthares-kwai-runner"
STATE_MARKER = "CF12_STATE_JSON:"
DO_SQL_READ_WARN = 4_000_000
DO_SQL_WRITE_WARN = 80_000
STAGES = ((70000, "critical"), (50000, "reduced"), (30000, "warning"))
OPTIONAL = (
    "anthares-cf02-stage-r0725",
    "anthares-cf03-qa-r0725",
    "anthares-video-studio-journal-c11-stage",
)
SECONDARY = ("anthares-ara-reserva", "anthares-ara-backup")
ESSENTIAL = frozenset((
    "anthares-control",
    "anthares-ara-mcp",
    "anthares-ara-neon-standby",
    "anthares-remote-control",
    "anthares-reserva-browser",
    "anthares-video-studio",
    "anthares-video-studio-journal",
    "anthares-git-independent",
    "anthares-tiktok-worker",
    "anthares-x-vault",
    "anthares-wordpress-mirror-scheduler",
    "anthares-cortes-neon-edge-ha",
    "anthares-cortes-queue-ha",
    "anthares-cortes-tiktok-ha",
    "anthares-cortes-tiktok-lucas4-ha",
))
ISSUE_NUMBER = int(os.environ.get("CF12_ISSUE_NUMBER", "0") or 0)
CF_API = "https://api.cloudflare.com/client/v4"
GH_API = "https://api.github.com"


def stage_for(requests):
    for threshold, value in STAGES:
        if requests >= threshold:
            return value
    return "normal"


def targets_for(stage):
    if stage == "critical":
        return OPTIONAL + SECONDARY
    if stage == "reduced":
        return OPTIONAL
    return ()


def approved(script):
    if script in ESSENTIAL:
        raise RuntimeError("CF12_ESSENTIAL_RESOURCE_PROTECTED")
    if script not in OPTIONAL + SECONDARY:
        raise RuntimeError("CF12_UNKNOWN_RESOURCE_REFUSED")


def call(method, url, token, payload=None, github=False):
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json" if github else "application/json",
        "User-Agent": "Anthares-CF12-QuotaGuard/1",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    if github:
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
    except urllib.error.HTTPError as err:
        raise RuntimeError(
            ("CF12_GITHUB_HTTP_" if github else "CF12_CLOUDFLARE_HTTP_") + str(err.code)
        ) from None
    except Exception as err:
        raise RuntimeError("CF12_HTTP_UNAVAILABLE_" + type(err).__name__) from None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        raise RuntimeError("CF12_API_INVALID_JSON") from None


def cf(method, path, token, payload=None):
    result = call(method, CF_API + path, token, payload)
    if not isinstance(result, dict) or result.get("success") is not True:
        raise RuntimeError("CF12_CF_API_REFUSED")
    return result.get("result")


def gh(method, path, token, payload=None):
    return call(method, GH_API + path, token, payload, github=True)


def observed_request_total(token, now):
    begin = now.replace(hour=0, minute=0, second=0, microsecond=0)
    query = """query($acc:string,$start:string,$end:string) {
      viewer { accounts(filter:{accountTag:$acc}) {
        workersInvocationsAdaptive(limit:10000,filter:{
          datetime_geq:$start,datetime_lt:$end
        }) { dimensions {scriptName status} sum {requests errors} }
      }}
    }"""
    variables = {
        "acc": ACCOUNT,
        "start": begin.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    data = call(
        "POST",
        CF_API + "/graphql",
        token,
        {"query": query, "variables": variables},
    )
    if not isinstance(data, dict) or data.get("errors"):
        raise RuntimeError("CF12_GRAPHQL_QUERY_FAILED")
    accounts = (((data.get("data") or {}).get("viewer") or {}).get("accounts") or [])
    if len(accounts) != 1:
        raise RuntimeError("CF12_GRAPHQL_ACCOUNT_MISMATCH")
    rows = accounts[0].get("workersInvocationsAdaptive")
    if not isinstance(rows, list) or len(rows) >= 10000:
        raise RuntimeError("CF12_GRAPHQL_INCOMPLETE")
    totals = {}
    errors = 0
    for row in rows:
        name = ((row.get("dimensions") or {}).get("scriptName") or "(unknown)")
        summed = row.get("sum") or {}
        value = int(summed.get("requests") or 0)
        if value < 0:
            raise RuntimeError("CF12_GRAPHQL_INVALID_COUNT")
        totals[name] = totals.get(name, 0) + value
        errors += int(summed.get("errors") or 0)
    return sum(totals.values()), errors, totals


def observed_do_sql_usage(token, now):
    # SQLite quota is independent of Workers request count. Read per-day
    # GraphQL accounting without invoking the Durable Object itself.
    query = """query($accountTag:String!,$day:Date){
      viewer{accounts(filter:{accountTag:$accountTag}){
        durableObjectsPeriodicGroups(filter:{date:$day},limit:10000){
          dimensions{namespaceId}sum{rowsRead rowsWritten}
        }
      }}
    }"""
    data = call(
        "POST", CF_API + "/graphql", token,
        {"query": query, "variables": {
            "accountTag": ACCOUNT, "day": now.date().isoformat()}},
    )
    if not isinstance(data, dict) or data.get("errors"):
        raise RuntimeError("CF12_DO_SQL_GRAPHQL_UNAVAILABLE")
    accounts = (((data.get("data") or {}).get("viewer") or {}).get("accounts") or [])
    if len(accounts) != 1:
        raise RuntimeError("CF12_DO_SQL_ACCOUNT_MISMATCH")
    rows = accounts[0].get("durableObjectsPeriodicGroups")
    if not isinstance(rows, list) or len(rows) >= 10000:
        raise RuntimeError("CF12_DO_SQL_DATA_INCOMPLETE")
    totals = {"rowsRead": 0, "rowsWritten": 0}
    namespaces = {}
    for row in rows:
        values = row.get("sum") or {}
        ns = (row.get("dimensions") or {}).get("namespaceId") or "unknown"
        for key in totals:
            val = int(values.get(key) or 0)
            if val < 0:
                raise RuntimeError("CF12_DO_SQL_INVALID_METRIC")
            totals[key] += val
            namespaces.setdefault(ns, {"rowsRead": 0, "rowsWritten": 0})[key] += val
    return totals, namespaces


def empty_state(day):
    return {"date": day, "level": "normal", "managed_disabled": [], "last_count": 0}


def read_state(github_token):
    if ISSUE_NUMBER <= 0:
        raise RuntimeError("CF12_ISSUE_NOT_CONFIGURED")
    issue = gh("GET", "/repos/" + REPO + "/issues/" + str(ISSUE_NUMBER), github_token)
    if not isinstance(issue, dict) or issue.get("title") != "CF12 | Controle preventivo da franquia Cloudflare":
        raise RuntimeError("CF12_WRONG_CONTROL_ISSUE")
    body = str(issue.get("body") or "")
    line = next((x[len(STATE_MARKER):] for x in body.splitlines()
                 if x.startswith(STATE_MARKER)), None)
    if line is None:
        raise RuntimeError("CF12_NO_STATE")
    try:
        state = json.loads(line)
    except ValueError:
        raise RuntimeError("CF12_STATE_INVALID") from None
    if not isinstance(state, dict) or not isinstance(state.get("managed_disabled"), list):
        raise RuntimeError("CF12_STATE_FORMAT_INVALID")
    for script in state["managed_disabled"]:
        approved(script)
    if not isinstance(state.get("date"), str):
        raise RuntimeError("CF12_STATE_DATE_INVALID")
    return state


def persist_state(github_token, state):
    body = (
        "Guarda de cota Cloudflare, executada fora da conta Cloudflare. "
        "A lista managed_disabled contém apenas entradas workers.dev desligadas por esta automação.\n"
        "Serviços essenciais, banco, filas, dispositivo remoto e autenticação permanecem ativos.\n\n"
        + STATE_MARKER + json.dumps(state, separators=(",", ":"), sort_keys=True) + "\n"
    )
    gh("PATCH", "/repos/" + REPO + "/issues/" + str(ISSUE_NUMBER),
       github_token, {"body": body})


def notify(github_token, now, level, count, details):
    body = (
        "CF12 " + level.upper() + " | " + now.strftime("%Y-%m-%dT%H:%M:%SZ") +
        " | invocações Workers UTC: " + str(count) +
        "\n" + details +
        "\nServiços essenciais Anthares Remote, MCP, Neon, controle, filas privadas e mídia preservados."
    )
    gh("POST", "/repos/" + REPO + "/issues/" + str(ISSUE_NUMBER) + "/comments",
       github_token, {"body": body})


def subdomain(token, script):
    approved(script)
    path = "/accounts/" + ACCOUNT + "/workers/scripts/" + script + "/subdomain"
    data = cf("GET", path, token)
    if not isinstance(data, dict) or not isinstance(data.get("enabled"), bool):
        raise RuntimeError("CF12_SUBDOMAIN_STATE_UNAVAILABLE_" + script)
    return data


def change_subdomain(token, script, enabled):
    current = subdomain(token, script)
    if current["enabled"] == enabled:
        return False
    path = "/accounts/" + ACCOUNT + "/workers/scripts/" + script + "/subdomain"
    payload = {"enabled": enabled}
    if isinstance(current.get("previews_enabled"), bool):
        payload["previews_enabled"] = current["previews_enabled"]
    result = cf("POST", path, token, payload)
    if not isinstance(result, dict) or result.get("enabled") is not enabled:
        raise RuntimeError("CF12_SUBDOMAIN_WRITE_UNCERTAIN_" + script)
    return True


def restore_yesterday(cloudflare_token, github_token, state, current_date):
    if state["date"] == current_date:
        return state
    # Daily quota resets at 00:00 UTC. Only resources recorded as disabled
    # by CF12 can be restored, preserving administrator-disabled scripts.
    while state["managed_disabled"]:
        script = state["managed_disabled"][0]
        change_subdomain(cloudflare_token, script, True)
        state["managed_disabled"].pop(0)
        persist_state(github_token, state)
        print("CF12_RESTORED " + script, flush=True)
    if state["date"] != current_date:
        previous_day = state["date"]
        summary = {
            "utc_day": previous_day,
            "last_count_sample": int(state.get("last_count") or 0),
            "health_probes": int(state.get("health_probes") or 0),
            "observed_1027": int(state.get("observed_1027") or 0),
            "sample_errors": int(state.get("sample_errors") or 0)
        }
        # Keep a rolling 15-day history in issue state. Unlike new issue
        # comments, PATCHing issue state does not email a daily notification.
        summaries = state.get("daily_summaries") or []
        if not isinstance(summaries, list):
            raise RuntimeError("CF12_SUMMARY_STATE_INVALID")
        summaries = [row for row in summaries if isinstance(row, dict)
                     and row.get("utc_day") != previous_day]
        summaries.append(summary)
        summaries = sorted(summaries, key=lambda row: str(row.get("utc_day") or ""))[-15:]
        state = empty_state(current_date)
        state["daily_summaries"] = summaries
        persist_state(github_token, state)
        print("CF12_DAILY_SUMMARY_RETAINED " + json.dumps(summary, sort_keys=True), flush=True)
    return state


def apply(cloudflare_token, github_token, state, target_level, count, now):
    wanted = targets_for(target_level)
    for script in wanted:
        approved(script)
        if script not in state["managed_disabled"]:
            current = subdomain(cloudflare_token, script)
            if current["enabled"] is False:
                # Disabled by administrator or another operator: never own it.
                print("CF12_ALREADY_DISABLED_EXTERNALLY " + script, flush=True)
                continue
            # Record intent before Cloudflare mutation so the next run can
            # restore even if the connection is lost after Cloudflare writes.
            state["managed_disabled"].append(script)
            persist_state(github_token, state)
        changed = change_subdomain(cloudflare_token, script, False)
        print("CF12_DISABLED " + script + " " + str(changed), flush=True)
    previous = state["level"]
    state["level"] = target_level
    state["last_count"] = count
    persist_state(github_token, state)
    if previous != target_level:
        details = {
            "warning": "Aviso de 30.000 invocações; modo normal preservado.",
            "reduced": "50.000: entradas públicas de homologação reduzidas.",
            "critical": "70.000: entradas HTTP legadas ARA de reserva/backup temporariamente suspensas.",
            "normal": "Franquia abaixo de 30.000; sem alterações.",
        }[target_level]
        notify(github_token, now, target_level, count, details)


def simulate():
    expected = {
        0: "normal", 29999: "normal", 30000: "warning",
        49999: "warning", 50000: "reduced", 69999: "reduced",
        70000: "critical", 100000: "critical",
    }
    for count, level in expected.items():
        assert stage_for(count) == level
    assert DO_SQL_READ_WARN < 5_000_000 and DO_SQL_WRITE_WARN < 100_000
    assert set(targets_for("warning")) == set()
    assert set(targets_for("reduced")) == set(OPTIONAL)
    assert set(targets_for("critical")) == set(OPTIONAL + SECONDARY)
    assert not (set(targets_for("critical")) & ESSENTIAL)
    try:
        approved("anthares-ara-mcp")
    except RuntimeError:
        pass
    else:
        raise AssertionError("essential protection missing")
    print("CF12_POLICY_OK 30000=warning 50000=reduced 70000=critical")
    print("CF12_ESSENTIAL_PROTECTED=1 CF12_ZERO_MUTATIONS=1")


def endpoint_health():
    # GitHub's independent network samples Workers ingress response codes.
    # Error 1027 can be rejected before an invocation reaches Worker Analytics.
    hosts = (
        "anthares-control.anthares1.workers.dev",
        "anthares-ara-neon-standby.anthares1.workers.dev",
        "anthares-ara-mcp.anthares1.workers.dev",
    )
    failures = 0
    quota_1027 = 0
    for host in hosts:
        request = urllib.request.Request(
            "https://" + host + "/health", headers={
                "User-Agent": "Anthares-CF12-QuotaHealth/1",
                "Accept": "application/json",
            })
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                status = response.status
                body = response.read(1024)
        except urllib.error.HTTPError as err:
            status = err.code
            body = err.read(1024)
        except Exception as err:
            failures += 1
            print("CF12_PROBE_UNAVAILABLE " + host + " " + type(err).__name__)
            continue
        if b"1027" in body or status == 1027:
            quota_1027 += 1
            failures += 1
            print("CF12_QUOTA_1027 " + host)
        elif status != 200:
            failures += 1
            print("CF12_PROBE_BAD_STATUS " + host + " " + str(status))
    return len(hosts), quota_1027, failures


def main():
    mode = os.environ.get("CF12_MODE", "run")
    if mode == "simulate":
        simulate()
        return
    if mode not in ("run", "rollback"):
        raise RuntimeError("CF12_MODE_NOT_ALLOWED")
    cloudflare_token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    github_token = os.environ.get("GITHUB_TOKEN", "")
    if len(cloudflare_token) < 15 or len(github_token) < 10:
        raise RuntimeError("CF12_AUTH_MISSING")
    now = dt.datetime.now(dt.timezone.utc)
    day = now.date().isoformat()
    state = read_state(github_token)
    if mode == "rollback":
        while state["managed_disabled"]:
            script = state["managed_disabled"][0]
            change_subdomain(cloudflare_token, script, True)
            state["managed_disabled"].pop(0)
            persist_state(github_token, state)
        state["manual_hold_date"] = day
        state["level"] = "manual_override"
        persist_state(github_token, state)
        notify(github_token, now, "manual_rollback", state.get("last_count", 0),
               "Entradas restauradas; ações automáticas de redução pausadas até 00:00 UTC.")
        print("CF13_ROLLBACK_DONE", json.dumps({"date":day,"state":state},sort_keys=True))
        return
    # An unresolved prior-day restore blocks fresh actions.
    state = restore_yesterday(cloudflare_token, github_token, state, day)
    count, errors, workers = observed_request_total(cloudflare_token, now)
    try:
        sql_usage, sql_namespaces = observed_do_sql_usage(cloudflare_token, now)
    except RuntimeError as ex:
        sql_usage, sql_namespaces = None, {}
        print("CF12_DO_SQL_UNAVAILABLE " + str(ex), flush=True)
    probes, errors_1027, probe_errors = endpoint_health()
    state["health_probes"] = int(state.get("health_probes") or 0) + probes
    state["observed_1027"] = int(state.get("observed_1027") or 0) + errors_1027
    state["sample_errors"] = int(state.get("sample_errors") or 0) + probe_errors
    persist_state(github_token, state)
    if sql_usage is not None:
        state["sql_usage"] = sql_usage
        if (sql_usage["rowsRead"] >= DO_SQL_READ_WARN or
                sql_usage["rowsWritten"] >= DO_SQL_WRITE_WARN):
            if state.get("sql_warning_date") != day:
                state["sql_warning_date"] = day
                persist_state(github_token, state)
                notify(github_token, now, "do_sql_warning", count,
                       "Durable Objects SQLite chegando ao limite Free: " +
                       json.dumps({"utc_day": day, **sql_usage}, sort_keys=True))
    if errors_1027:
        notify(github_token, now, "quota_1027", count,
               "Falha 1027 observada no monitor externo; proteger serviços essenciais.")
    if state.get("manual_hold_date") == day:
        print("CF12_MANUAL_HOLD", json.dumps({"requests":count,"utc_day":day,"essential_preserved":True}))
        return
    level = stage_for(count)
    apply(cloudflare_token, github_token, state, level, count, now)
    print("CF12_LIVE", json.dumps({
        "utc_day": day,
        "requests": count,
        "worker_errors": errors,
        "do_sql_usage": sql_usage,
        "do_sql_namespaces": sql_namespaces,
        "level": level,
        "top3": sorted(workers.items(), key=lambda x: -x[1])[:3],
        "owned_disabled": state["managed_disabled"],
        "essential_preserved": True
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        print("CF12_FAIL_CLOSED " + str(ex), file=sys.stderr, flush=True)
        sys.exit(2)
