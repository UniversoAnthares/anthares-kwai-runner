#!/usr/bin/env python3
"""Read-only diagnosis of Buffer's Pinterest board metadata via alternate resolvers."""
from __future__ import annotations
import json
import os
import sys
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from social_adapters.buffer_three_channels import api, BufferBlocked, PINNED_CHANNELS, PINTEREST_PUBLIC_BOARD_ID

def inspect(name,query,extract):
    try:
        payload=api(query)
        data=extract(payload)
        print("PIN_BUFFER_"+name+"=OK",flush=True)
        return data
    except BufferBlocked as err:
        reason=str(err)
        kind=reason if reason.startswith("BUFFER_") else "BUFFER_UNKNOWN"
        print("PIN_BUFFER_"+name+"="+kind,flush=True)
    except (TypeError,ValueError,KeyError):
        print("PIN_BUFFER_"+name+"=RESPONSE_INVALID",flush=True)
    return None

def main():
    ch=PINNED_CHANNELS["pinterest"][0]
    cid=json.dumps(ch)
    orgs=inspect("ORGANIZATIONS","query { account { organizations { id } } }",
                 lambda x:(x.get("account") or {}).get("organizations") or [])
    inspect("CHANNEL_ID_ONLY",f"query {{ channel(input: {{ id: {cid} }}) {{ id service }} }}",
            lambda x:(x.get("channel") or {}).get("id"))
    inspect("CHANNEL_METADATA_TYPE",f"query {{ channel(input: {{ id: {cid} }}) {{ id metadata {{ __typename }} }} }}",
            lambda x:(x.get("channel") or {}).get("metadata"))
    def fromrow(x):
        row=x.get("channel") or {}
        boards=(row.get("metadata") or {}).get("boards") or []
        print("PIN_BUFFER_BOARD_FOUND="+str(any(str(b.get("serviceId"))==PINTEREST_PUBLIC_BOARD_ID for b in boards)).lower())
        return boards
    inspect("DIRECT_BOARD",f"query {{ channel(input: {{ id: {cid} }}) {{ id metadata {{ ... on PinterestMetadata {{ boards {{ serviceId }} }} }} }} }}",fromrow)
    for org in (orgs or [])[:4]:
        oid=str(org.get("id") or "")
        if not oid:continue
        q='query { channels(input: { organizationId: '+json.dumps(oid)+' }) { id service metadata { ... on PinterestMetadata { boards { serviceId } } } } }'
        def fromlist(payload):
            rows=payload.get("channels") or []
            matched=[c for c in rows if c.get("id")==ch]
            boards=(matched[0].get("metadata") or {}).get("boards") or [] if matched else []
            print("PIN_BUFFER_CHANNELS_BOARD_FOUND="+str(any(str(b.get("serviceId"))==PINTEREST_PUBLIC_BOARD_ID for b in boards)).lower())
            return boards
        inspect("CHANNELS_METADATA",q,fromlist)
    return 0

if __name__=="__main__":
    sys.exit(main())
