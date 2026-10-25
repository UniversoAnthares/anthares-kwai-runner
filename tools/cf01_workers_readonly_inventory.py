#!/usr/bin/env python3
"""CF-01 scoped read-only inventory of one existing Cloudflare Worker.

Credential stays in GitHub Actions Secrets. Emits only allowlisted status
codes/metadata; no account IDs, token values, API response bodies or names.
No PATCH/PUT/POST/DELETE, no deploy, no KV or Durable Object reads.
"""
import json
import os
import urllib.error
import urllib.request

ACCOUNT_ID = "5c24be052e5144391f73a8e03491e88e"
WORKER = "anthares-control"
BASE = "https://api.cloudflare.com/client/v4"
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")
ALLOWED_BINDINGS = {"ANTHARES_STATE", "ANTHARES_QUEUE"}
URLS = {
    "account": f"/accounts/{ACCOUNT_ID}",
    "account_settings": f"/accounts/{ACCOUNT_ID}/workers/account-settings",
    "worker_settings": f"/accounts/{ACCOUNT_ID}/workers/scripts/{WORKER}/settings",
    "schedule": f"/accounts/{ACCOUNT_ID}/workers/scripts/{WORKER}/schedules",
    "subscriptions": f"/accounts/{ACCOUNT_ID}/subscriptions",
}
def get_json(path, token=None):
    address = BASE + path if path.startswith("/") else path
    headers = {"Accept":"application/json", "User-Agent":"anthares-cf01-audit/1"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req=urllib.request.Request(address, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req,timeout=15) as response:
            raw=response.read(2_000_000)
            data=json.loads(raw)
            return {"http":response.status,"result":data.get("result") if isinstance(data,dict) and "result" in data else data}
    except urllib.error.HTTPError as e:
        return {"http":int(e.code),"result":None}
    except Exception:
        return {"http":0,"result":None}
def plan_type(result):
    # Payment/contract must be proven by the authenticated account response;
    # default_usage_model alone is NOT proof of a Workers Free/Paid subscription.
    if not isinstance(result,list):
        return "UNKNOWN"
    tokens=[]
    for item in result:
        if not isinstance(item,dict):
            continue
        obj=item.get("rate_plan") or item.get("plan") or {}
        text=" ".join(str(obj.get(k,"")) for k in ("id","name","public_name")) if isinstance(obj,dict) else str(obj)
        if "workers" in text.lower():
            tokens.append(text.lower())
    if not tokens:
        return "UNKNOWN"
    if any("paid" in t or "standard" in t for t in tokens):
        return "PAID_SUBSCRIPTION"
    if any("free" in t for t in tokens):
        return "FREE_SUBSCRIPTION"
    return "WORKERS_SUBSCRIPTION_UNCLASSIFIED"
def main():
    if not TOKEN:
        print("CF01_INVENTORY="+json.dumps({"status":"BLOCKED","reason":"CLOUDFLARE_API_TOKEN_UNAVAILABLE"}))
        return 2
    fetched={key:get_json(path,TOKEN) for key,path in URLS.items()}
    settings=fetched["worker_settings"]["result"]
    bindings=settings.get("bindings",[]) if isinstance(settings,dict) else []
    binding_names=sorted({x.get("name","") for x in bindings if isinstance(x,dict)} & ALLOWED_BINDINGS)
    binding_types={x.get("name"):x.get("type","UNKNOWN") for x in bindings if isinstance(x,dict) and x.get("name") in ALLOWED_BINDINGS}
    schedule=fetched["schedule"]["result"]
    schedules=schedule if isinstance(schedule,list) else (schedule.get("schedules",[]) if isinstance(schedule,dict) else [])
    cron_found=any("*/5" in str(x.get("cron","")) for x in schedules if isinstance(x,dict))
    account=fetched["account"]["result"]
    owner_confirmed=isinstance(account,dict) and account.get("id")==ACCOUNT_ID
    plan=plan_type(fetched["subscriptions"]["result"])
    health=get_json("https://anthares-control.anthares1.workers.dev/health")
    live=health["result"]
    # The public health endpoint is a standalone JSON object, not wrapped by 'result'.
    service_live=isinstance(live,dict) and live.get("ok") is True and live.get("service")=="anthares-control"
    result={
        "inventory_id":"CF01-20261025-WORKER",
        "worker":"anthares-control",
        "status":"PASS" if owner_confirmed and len(binding_names)==2 and service_live and plan!="UNKNOWN" and fetched["account_settings"]["http"]==200 else "PARTIAL",
        "api_http":{key:value["http"] for key,value in fetched.items()},
        "account_owner_verified":owner_confirmed,
        "binding_names":binding_names,
        "binding_types":binding_types,
        "cron_5min_verified":cron_found,
        "subscription_plan":plan,
        "default_usage_model":fetched["account_settings"]["result"].get("default_usage_model","UNKNOWN") if isinstance(fetched["account_settings"]["result"],dict) else "UNKNOWN",
        "live_health_http":health["http"],
        "live_health_verified":service_live,
        "price_source":"https://developers.cloudflare.com/workers/platform/pricing/",
        "limit_source":"https://developers.cloudflare.com/workers/platform/limits/",
        "writes":0,
        "secret_values_emitted":False,
    }
    print("CF01_INVENTORY="+json.dumps(result,sort_keys=True))
    # Fail closed: CI must not greenwash missing administrative authorization.
    return 0 if result["status"]=="PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
