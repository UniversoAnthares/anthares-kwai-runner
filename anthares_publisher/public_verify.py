#!/usr/bin/env python3
"""Independent, credential-free HTTP verification of an observed public post URL.

A matching URL shape alone is insufficient. Require a public HTTPS response
from the target platform. Never send cookies, bearer tokens or credentials.
"""
import argparse
import json
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from anthares_publisher.contract import PublicationEvidence,validate_evidence

class PublicVerificationError(ValueError):
    pass

class PlatformOnlyRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        parsed=urlsplit(newurl)
        if parsed.scheme!="https" or parsed.hostname not in ("kwai.com","www.kwai.com"):
            raise PublicVerificationError("redirect left allowed Kwai domain")
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def verify(url,external_id,account="lucasrosalem",opener=None):
    validate_evidence(PublicationEvidence("kwai",account,external_id,url),"kwai",account)
    opener=opener or urllib.request.build_opener(PlatformOnlyRedirect)
    request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 AntharesPublicPostVerifier/1.0","Accept":"text/html"},method="GET")
    try:
        with opener.open(request,timeout=12) as response:
            status=response.status
            final=response.geturl()
            content_type=response.headers.get("Content-Type","").lower()
            # Read a bounded amount; never print response body or user data.
            sample=response.read(131072)
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        raise PublicVerificationError("public post unavailable") from exc
    validate_evidence(PublicationEvidence("kwai",account,external_id,final),"kwai",account)
    if status!=200 or "text/html" not in content_type or len(sample)<32:
        raise PublicVerificationError("public post did not return an HTML document")
    # This establishes public HTTP reachability, not server-side ownership.
    return {"http_public":True,"status":status,"url":final,
            "account_claim":account,"server_identity_verified":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--url",required=True)
    p.add_argument("--post-id",required=True)
    p.add_argument("--account",default="lucasrosalem")
    a=p.parse_args()
    try:
        out=verify(a.url,a.post_id,a.account)
    except (ValueError,PublicVerificationError) as exc:
        print("KWAI_PUBLIC_URL_VERIFICATION_FAILED="+type(exc).__name__)
        return 1
    print("KWAI_PUBLIC_URL_HTTP_VERIFIED=1")
    print(json.dumps(out,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
