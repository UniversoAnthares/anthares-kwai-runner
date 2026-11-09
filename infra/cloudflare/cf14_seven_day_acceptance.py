#!/usr/bin/env python3
"""CF-14 seven *complete* UTC day acceptance, externally executed by GitHub."""
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request

CF_ACCOUNT = "5c24be052e5144391f73a8e03491e88e"
REPO = "UniversoAnthares/anthares-kwai-runner"
FIRST_FULL_DAY = dt.date(2026, 11, 8)
QUOTA_ISSUE = 2160
ACCEPTANCE_ISSUE = 2162
GRAPH = "https://api.cloudflare.com/client/v4/graphql"


def http(url, token=None, payload=None):
    headers = {"Accept": "application/json", "User-Agent": "Anthares-CF14-Acceptance/1"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        url, method="POST" if payload is not None else "GET",
        data=json.dumps(payload).encode() if payload is not None else None,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
    except urllib.error.HTTPError as ex:
        raise RuntimeError("CF14_HTTP_" + str(ex.code)) from None
    except Exception as ex:
        raise RuntimeError("CF14_UNAVAILABLE_" + type(ex).__name__) from None
    if not data:
        return {}
    return json.loads(data)


def github(method, path, token, body=None):
    url = "https://api.github.com" + path
    headers = {"Authorization": "Bearer " + token,
               "Accept": "application/vnd.github+json",
               "Content-Type": "application/json",
               "X-GitHub-Api-Version": "2022-11-28"}
    req = urllib.request.Request(
        url, data=json.dumps(body).encode() if body is not None else None,
        headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
    except urllib.error.HTTPError as ex:
        raise RuntimeError("CF14_GITHUB_HTTP_" + str(ex.code)) from None
    return json.loads(raw) if raw else {}


def day_analytics(cloudflare_token, day):
    start = dt.datetime.combine(day, dt.time(0), dt.timezone.utc)
    end = start + dt.timedelta(days=1)
    query = """query($acc:string,$start:string,$end:string){
      viewer {accounts(filter:{accountTag:$acc}){
        workersInvocationsAdaptive(limit:10000,filter:{
          datetime_geq:$start,datetime_lt:$end}){
          dimensions{scriptName status}sum{requests errors subrequests}
        }
      }}
    }"""
    variables = {"acc": CF_ACCOUNT,
                 "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "end": end.strftime("%Y-%m-%dT%H:%M:%SZ")}
    data = http(GRAPH, cloudflare_token, {"query": query, "variables": variables})
    if data.get("errors"):
        raise RuntimeError("CF14_GRAPHQL_RESPONSE_INVALID")
    accounts = (((data.get("data") or {}).get("viewer") or {}).get("accounts") or [])
    if len(accounts) != 1:
        raise RuntimeError("CF14_ACCOUNT_MISMATCH")
    rows = accounts[0].get("workersInvocationsAdaptive")
    if not isinstance(rows, list) or len(rows) >= 10000:
        raise RuntimeError("CF14_INCOMPLETE_DATA")
    return {
        "utc_day": day.isoformat(),
        "workers_requests": sum(int((r.get("sum") or {}).get("requests") or 0) for r in rows),
        "worker_errors": sum(int((r.get("sum") or {}).get("errors") or 0) for r in rows),
        "subrequests": sum(int((r.get("sum") or {}).get("subrequests") or 0) for r in rows),
    }


def day_do_sql_analytics(cloudflare_token, day):
    query = """query($accountTag:String!,$day:Date){
      viewer {accounts(filter:{accountTag:$accountTag}){
        durableObjectsPeriodicGroups(filter:{date:$day},limit:10000){
          dimensions{date namespaceId}sum{rowsRead rowsWritten}
        }
      }}
    }"""
    data = http(GRAPH, cloudflare_token, {"query": query, "variables": {
        "accountTag": CF_ACCOUNT, "day": day.isoformat()}})
    if data.get("errors"):
        raise RuntimeError("CF14_DO_SQL_GRAPHQL_INVALID")
    accounts = (((data.get("data") or {}).get("viewer") or {}).get("accounts") or [])
    if len(accounts) != 1:
        raise RuntimeError("CF14_DO_SQL_ACCOUNT_MISMATCH")
    rows = accounts[0].get("durableObjectsPeriodicGroups")
    if not isinstance(rows, list) or len(rows) >= 10000:
        raise RuntimeError("CF14_DO_SQL_DATA_INCOMPLETE")
    return {
        "do_sql_rows_read": sum(int((r.get("sum") or {}).get("rowsRead") or 0) for r in rows),
        "do_sql_rows_written": sum(int((r.get("sum") or {}).get("rowsWritten") or 0) for r in rows),
    }


def probe_summaries(gh_token):
    records = {}
    base = "/repos/" + REPO + "/issues/" + str(QUOTA_ISSUE) + "/comments"
    for page in range(1, 6):
        comments = github("GET", base + "?per_page=100&page=" + str(page), gh_token)
        if not isinstance(comments, list):
            raise RuntimeError("CF14_COMMENTS_UNAVAILABLE")
        for item in comments:
            text = item.get("body") or ""
            match = re.search(r"CF12_DAILY_SUMMARY (\{[^\n]*\})", text)
            if not match:
                continue
            try:
                row = json.loads(match.group(1))
            except ValueError:
                continue
            if isinstance(row, dict) and row.get("utc_day"):
                records[str(row["utc_day"])] = row
        if len(comments) < 100:
            break
    # New CF12 reports are kept in the issue body to avoid daily email alerts.
    # Previously published comment summaries remain valid for the same window.
    issue = github("GET", "/repos/" + REPO + "/issues/" + str(QUOTA_ISSUE), gh_token)
    line = next((entry[len("CF12_STATE_JSON:"):]
                 for entry in str(issue.get("body") or "").splitlines()
                 if entry.startswith("CF12_STATE_JSON:")), None)
    if line is None:
        raise RuntimeError("CF14_CF12_STATE_UNAVAILABLE")
    try:
        state = json.loads(line)
    except ValueError:
        raise RuntimeError("CF14_CF12_STATE_INVALID") from None
    stored = state.get("daily_summaries") or {}
    if not isinstance(stored, dict):
        raise RuntimeError("CF14_DAILY_HISTORY_INVALID")
    for day, row in stored.items():
        if not isinstance(row, dict) or row.get("utc_day") != day:
            raise RuntimeError("CF14_DAILY_HISTORY_INVALID")
        records[day] = row
    return records


def live_controls():
    services = (
        ("mcp", "https://anthares-ara-mcp.anthares1.workers.dev/health"),
        ("neon", "https://anthares-ara-neon-standby.anthares1.workers.dev/health"),
        ("control", "https://anthares-control.anthares1.workers.dev/health"),
    )
    health = {}
    for name, url in services:
        result = http(url)
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise RuntimeError("CF14_LIVE_HEALTH_BAD_" + name)
        if name == "mcp" and result.get("device_connected") is not True:
            raise RuntimeError("CF14_REMOTE_DISCONNECTED")
        health[name] = True
    return health


def main():
    now = dt.datetime.now(dt.timezone.utc)
    end = now.date()
    first = end - dt.timedelta(days=7)
    if first < FIRST_FULL_DAY:
        print("CF14_WAIT_FOR_SEVEN_FULL_UTC_DAYS",
              json.dumps({"today_utc": end.isoformat(),
                          "earliest_full_start": FIRST_FULL_DAY.isoformat(),
                          "earliest_acceptable_end": "2026-11-15T00:00:00Z"}))
        return
    cf_token = os.getenv("CLOUDFLARE_API_TOKEN", "")
    gh_token = os.getenv("GITHUB_TOKEN", "")
    if len(cf_token) < 15 or len(gh_token) < 10:
        raise RuntimeError("CF14_AUTH_MISSING")
    issue = github("GET", "/repos/" + REPO + "/issues/" + str(ACCEPTANCE_ISSUE), gh_token)
    if issue.get("title") != "CF14 | Aceite de sete dias UTC da cota Cloudflare":
        raise RuntimeError("CF14_WRONG_ISSUE")
    if issue.get("state") == "closed":
        print("CF14_ACCEPTANCE_ALREADY_CLOSED")
        return
    summaries = probe_summaries(gh_token)
    days = [first + dt.timedelta(days=i) for i in range(7)]
    rows = []
    for day in days:
        row = day_analytics(cf_token, day)
        row.update(day_do_sql_analytics(cf_token, day))
        rows.append(row)
    failures = []
    for row in rows:
        date = row["utc_day"]
        if row["workers_requests"] >= 30000:
            failures.append(date + ":quota_30000")
        if row["do_sql_rows_read"] >= 5000000:
            failures.append(date + ":do_sql_rows_read_limit")
        if row["do_sql_rows_written"] >= 100000:
            failures.append(date + ":do_sql_rows_written_limit")
        if row["worker_errors"] != 0:
            failures.append(date + ":worker_errors")
        sample = summaries.get(date)
        if not sample or int(sample.get("health_probes", 0)) < 60:
            failures.append(date + ":insufficient_external_probes")
        elif (int(sample.get("observed_1027", 0)) != 0 or
              int(sample.get("sample_errors", 0)) != 0):
            failures.append(date + ":external_probe_failed")
    try:
        controls = live_controls()
    except RuntimeError as ex:
        controls = {}
        failures.append(str(ex))
    print("CF14_WINDOW", json.dumps({
        "start": first.isoformat(), "end_exclusive": end.isoformat(),
        "daily": rows, "controls": controls, "failures": failures
    }, sort_keys=True))
    if failures:
        raise RuntimeError("CF14_ACCEPTANCE_CRITERIA_UNMET:" + ",".join(failures)[:400])
    details = ("CF14_ACCEPTED_7_FULL_UTC_DAYS\n" +
               json.dumps({"start":first.isoformat(),"last":days[-1].isoformat(),
                           "daily":rows,"remote_connected":True,
                           "1027_observed_in_external_probes":0}, sort_keys=True))
    github("POST","/repos/"+REPO+"/issues/"+str(ACCEPTANCE_ISSUE)+"/comments",gh_token,
           {"body":details})
    github("PATCH","/repos/"+REPO+"/issues/"+str(ACCEPTANCE_ISSUE),gh_token,
           {"state":"closed"})
    print("CF14_ACCEPTED_7_FULL_UTC_DAYS")


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        print("CF14_PENDING " + str(ex), file=sys.stderr)
        sys.exit(2)
