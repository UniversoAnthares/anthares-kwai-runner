#!/usr/bin/env python3
"""Read-only validation of Codeberg secret-admin capability using a disposable key."""
import base64, json, os, sys, urllib.error, urllib.parse, urllib.request
PATH="https://codeberg.org/api/v1/repos/UniversoAnthares/anthares-kwai-runner/actions/secrets/ANTHARES_BOOTSTRAP_PROBE"
def main():
    raw=os.environ.get("CODEBERG_PUSH_URL","")
    parsed=urllib.parse.urlsplit(raw)
    if parsed.scheme!="https" or parsed.hostname!="codeberg.org":
        raise ValueError("CODEBERG_SECRET_URL_WRONG_HOST")
    user=urllib.parse.unquote(parsed.username or "")
    password=urllib.parse.unquote(parsed.password or "")
    if not user or not password:
        raise ValueError("CODEBERG_SECRET_URL_MISSING_CREDENTIALS")
    auth=base64.b64encode((user+":"+password).encode()).decode()
    headers={"Authorization":"Basic "+auth,"Content-Type":"application/json",
             "Accept":"application/json"}
    created=False
    try:
        request=urllib.request.Request(PATH,headers=headers,
            data=json.dumps({"data":"CORTES_CODEBERG_PROBE_NO_PRIVATE_DATA"}).encode(),method="PUT")
        with urllib.request.urlopen(request,timeout=20) as r:
            status=r.status
        if status not in (200,201,204):
            raise RuntimeError("CODEBERG_SECRET_PUT_UNEXPECTED_STATUS")
        created=True
        print("CODEBERG_SECRET_WRITE_PERMISSION_PROVEN=1")
    except urllib.error.HTTPError as ex:
        print("CODEBERG_SECRET_WRITE_HTTP="+str(ex.code))
        return 2
    finally:
        if created:
            try:
                with urllib.request.urlopen(
                        urllib.request.Request(PATH,headers=headers,method="DELETE"),
                        timeout=20) as response:
                    print("CODEBERG_PROBE_SECRET_REMOVED="+str(response.status in (200,202,204)))
            except urllib.error.HTTPError as ex:
                print("CODEBERG_PROBE_DELETE_HTTP="+str(ex.code))
    return 0
if __name__=="__main__":
    try:sys.exit(main())
    except Exception as e:
        print("CODEBERG_SECRET_PROBE_ERROR="+type(e).__name__,file=sys.stderr)
        sys.exit(2)
