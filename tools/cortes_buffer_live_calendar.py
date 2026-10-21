#!/usr/bin/env python3
"""Authenticated, strictly read-only Buffer calendar for CORTES.

Prints effective posting schedule per channel in its declared timezone, plus
exact dueAt timestamps for queued posts. Never prints captions, access keys,
private organization identity or unsanitized remote API error messages.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from social_adapters.buffer_three_channels import (
    api, channels, validate_channel, PINNED_CHANNELS, BufferBlocked)

def main():
    found=channels()
    ids={service:entry[0] for service,entry in PINNED_CHANNELS.items()}
    by_id={}
    for service, channel_id in ids.items():
        c=validate_channel(service,channel_id,found)
        by_id[channel_id]=service
    channel_state={}
    for channel_id,service in by_id.items():
        query=("query CORTESBufferChannel { channel(input: { id: "+
               json.dumps(channel_id)+" }) { id timezone isQueuePaused "
               "postingSchedule { day paused times } } }")
        c=api(query).get("channel") or {}
        if c.get("id")!=channel_id:
            raise BufferBlocked("BUFFER_SCHEDULE_ID_MISMATCH:"+service)
        rows=c.get("postingSchedule")
        if not isinstance(rows,list):
            raise BufferBlocked("BUFFER_SCHEDULE_MISSING:"+service)
        zone=str(c.get("timezone") or "")
        print("BUFFER_CHANNEL service="+service+" timezone="+zone+
              " paused="+str(c.get("isQueuePaused")).lower(),flush=True)
        channel_state[service]={"channel_id":channel_id,"timezone":zone,
            "queue_paused":bool(c.get("isQueuePaused")),"weekly_schedule":[],"queued_posts":[]}
        for row in rows:
            day=str(row.get("day") or "").lower()
            paused=bool(row.get("paused"))
            times=sorted(str(t) for t in (row.get("times") or []))
            print("BUFFER_SLOT service="+service+" day="+day+
                  " paused="+str(paused).lower()+" times="+",".join(times),flush=True)
            channel_state[service]["weekly_schedule"].append(
                {"day":day,"paused":paused,"times":times})
    organization=api("query CORTESBufferOrganizations { account { organizations { id } } }")
    orgs=(organization.get("account") or {}).get("organizations") or []
    for org in orgs:
        oid=str(org.get("id") or "")
        if not oid:continue
        cursor=None
        for page in range(1,10):
            after=(", after: "+json.dumps(cursor)) if cursor else ""
            query=("query CORTESBufferQueue { posts(first: 50"+after+
                   ", input: { organizationId: "+json.dumps(oid)+
                   ", sort: [{field: dueAt, direction: asc}], "
                   "filter: { status: [scheduled], channelIds: "+
                   json.dumps(list(by_id))+" } }) { edges { node { id channelId "
                   "dueAt status schedulingType } } pageInfo { hasNextPage endCursor } } }")
            result=api(query).get("posts") or {}
            for entry in result.get("edges") or []:
                post=entry.get("node") or {}
                service=by_id.get(str(post.get("channelId") or ""))
                if not service:continue
                due=str(post.get("dueAt") or "")
                if not due:continue
                print("BUFFER_BOOKED service="+service+" dueAt="+due+
                      " post_id="+str(post.get("id") or "")[:60],flush=True)
                channel_state[service]["queued_posts"].append(
                    {"due_at_utc":due,"post_id":str(post.get("id") or "")})
            page_info=result.get("pageInfo") or {}
            if not page_info.get("hasNextPage"):break
            next_cursor=page_info.get("endCursor")
            if not next_cursor or next_cursor==cursor:
                raise BufferBlocked("BUFFER_PAGINATION_STALLED")
            cursor=next_cursor
        else:
            raise BufferBlocked("BUFFER_CALENDAR_PAGINATION_EXCEEDED")
    now=datetime.now(timezone.utc).isoformat()
    print("BUFFER_CALENDAR_OBSERVED_UTC="+now,flush=True)
    for service,v in channel_state.items():
        print("BUFFER_QUEUE_COUNT service="+service+" scheduled="+str(len(v["queued_posts"])),flush=True)
    path=Path("buffer-calendar-observation.json")
    path.write_text(json.dumps({"observed_at_utc":now,"channels":channel_state},
                               ensure_ascii=False,indent=2),encoding="utf-8")
    print("BUFFER_CALENDAR_AUDIT=PASS",flush=True)

if __name__=="__main__":
    try:main()
    except BufferBlocked as error:
        print("::error::BUFFER_CALENDAR_BLOCKED "+str(error),flush=True)
        sys.exit(2)
