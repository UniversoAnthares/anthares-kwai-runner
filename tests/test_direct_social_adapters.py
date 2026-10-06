import os, subprocess, json, sys

SCRIPT="social_adapters/direct_social.py"
def run(payload, env=None):
    e=os.environ.copy(); e.update(env or {})
    p=subprocess.run([sys.executable,SCRIPT],input=json.dumps(payload),text=True,capture_output=True,env=e)
    assert p.returncode==0,p.stderr
    return json.loads(p.stdout)

def test_instagram_auth_gate():
    for k in ["META_INSTAGRAM_ACCESS_TOKEN","META_INSTAGRAM_USER_ID"]: os.environ.pop(k,None)
    o=run({"platform":"instagram","account_id":"primary","media_url":"https://example.invalid/a.jpg"})
    assert o["status"]=="AUTH_REQUIRED" and o["destination_key"]=="instagram:primary"

def test_threads_auth_gate():
    os.environ.pop("THREADS_ACCESS_TOKEN",None)
    o=run({"platform":"threads","account_id":"primary","text":"probe"})
    assert o["status"]=="AUTH_REQUIRED" and o["destination_key"]=="threads:primary"

def test_x_paid_route_fail_closed():
    o=run({"platform":"x","account_id":"primary","text":"probe"},{"X_ALLOW_PAID_API":"0"})
    assert o["status"]=="BLOCKED_PAID_API" and o["destination_key"]=="x:primary"

def test_accounts_are_isolated():
    o=run({"platform":"threads","account_id":"secondary","text":"probe"})
    assert o["destination_key"]=="threads:secondary"

if __name__=="__main__":
    test_instagram_auth_gate(); test_threads_auth_gate(); test_x_paid_route_fail_closed(); test_accounts_are_isolated()
    print("SOCIAL_ADAPTER_CONTRACT=PROVEN")
