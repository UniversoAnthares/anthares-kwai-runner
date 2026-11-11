#!/usr/bin/env python3
"""Read actual Buffer post receipts to locate CORTES historical uncertainty.

Read-only operation. No media access, publishing, Neon changes, upload or tests.
Only exact matching of archived source URL fingerprints is considered evidence.
Missing matches remain uncertain and must never be blindly reposted.
"""
import hashlib
import json
import sys
from urllib.parse import urlsplit

from social_adapters.buffer_three_channels import api, PINNED_CHANNELS

# Each fingerprint is the first 24 hex digits of MD5(source media URL) in Neon.
# Jobs have neither remote Buffer IDs nor a verified social permalink.
EXPECTED = {
    "instagram": {
        "ea52733af3f494cd30179a1d": "c652b35312dd",
        "32c71c4c0fa1ae2119bccbc7": "4b66a3e5d3b4",
        "80dced27e41648fed23043a1": "293808e7fe0a",
        "73a47fc4bb7a126c83bdf4cd": "11fe6e0c39d7",
    },
    "linkedin": {
        "5c4a827ed8aa7f0fa2f23ea1": "0f7494c953ba",
        "340405c3b6d19864d24e7fd0": "205a239a73ad",
    },
    "pinterest": {
        "16a7a9e77dd01efbfffd3485": "e4905036adcc",
        "4bc6412a84654d27a5588f96": "ce8d96928622",
        "3743fae04e9b53ed6441bfa1": "ce835ec78b55",
        "70c9ef3ff00907a1b958380f": "9ac76d66a9db",
        "8751eb0c83c2a5e0178f1137": "b94be5a30941",
        "80dced27e41648fed23043a1": "17c048f2201f",
        "149d43644a4db7172fc03f63": "88f0128c91c5",
    },
}
VALID_HOST = {
    "instagram": {"www.instagram.com", "instagram.com"},
    "linkedin": {"www.linkedin.com", "linkedin.com"},
    "pinterest": {"www.pinterest.com", "pinterest.com", "br.pinterest.com"},
}
CUTOFF = "2026-10-19T00:00:00"
PAGE_SIZE = 50
MAX_PAGES = 18


def read_organizations():
    account = api("query CortesLegacyOrphanOrgs { account { organizations { id } } }")
    orgs = (account.get("account") or {}).get("organizations") or []
    if not (1 <= len(orgs) <= 6):
        raise RuntimeError("BUFFER_ORGANIZATIONS_UNVERIFIED")
    found = {}
    for organization in orgs:
        org_id = str(organization.get("id") or "")
        if not org_id:
            raise RuntimeError("BUFFER_ORG_ID_MISSING")
        query = ('query CortesLegacyOrphanChannels { channels(input: { organizationId: '
                 + json.dumps(org_id) + ' }) { id service } }')
        rows = api(query).get("channels") or []
        for service in EXPECTED:
            wanted = PINNED_CHANNELS[service][0]
            matched = [item for item in rows if str(item.get("id") or "") == wanted
                       and str(item.get("service") or "").lower() == service]
            if len(matched) > 1 or (matched and service in found):
                raise RuntimeError("BUFFER_CHANNEL_IDENTITY_AMBIGUOUS")
            if matched:
                found[service] = org_id
    if len(found) != len(EXPECTED):
        raise RuntimeError("BUFFER_TARGET_CHANNEL_MISSING")
    return found


def read_channel(service, org_id):
    target = PINNED_CHANNELS[service][0]
    refs = EXPECTED[service]
    cursor = None
    seen_cursors = set()
    matches = {ref: [] for ref in refs.values()}
    count = 0
    exhaustive = False
    for page in range(MAX_PAGES):
        after = "" if cursor is None else "after: " + json.dumps(cursor) + ","
        query = ('query CortesLegacyOrphanPosts { posts(first: ' + str(PAGE_SIZE) + ', '
                 + after + ' input: { organizationId: ' + json.dumps(org_id)
                 + ', sort: [{ field: createdAt, direction: desc }], '
                 + 'filter: { channelIds: [' + json.dumps(target)
                 + '] } }) { pageInfo { hasNextPage endCursor } '
                 + 'edges { node { id channelId status externalLink createdAt dueAt '
                 + 'assets { source } } } } }')
        connection = api(query).get("posts")
        if not isinstance(connection, dict):
            raise RuntimeError("BUFFER_POST_LIST_UNVERIFIED")
        edges = connection.get("edges")
        page_info = connection.get("pageInfo")
        if not isinstance(edges, list) or not isinstance(page_info, dict):
            raise RuntimeError("BUFFER_POST_PAGINATION_UNVERIFIED")
        dates = []
        for edge in edges:
            row = (edge or {}).get("node") or {}
            if str(row.get("channelId") or "") != target:
                raise RuntimeError("BUFFER_POST_WRONG_CHANNEL")
            count += 1
            created = str(row.get("createdAt") or "")
            if created:
                dates.append(created)
            ids = set()
            for asset in (row.get("assets") or []):
                src = str((asset or {}).get("source") or "").split("?", 1)[0]
                if not src:
                    continue
                key = hashlib.md5(src.encode("utf-8")).hexdigest()[:24]
                if key in refs:
                    ids.add(refs[key])
            for ref in ids:
                status = str(row.get("status") or "").lower()
                url = str(row.get("externalLink") or "")
                parsed = urlsplit(url)
                public_link = (url if status == "sent" and parsed.scheme == "https"
                               and parsed.hostname in VALID_HOST[service]
                               and not parsed.username and not parsed.password
                               else None)
                matches[ref].append({
                    "post_id": str(row.get("id") or "")[:100],
                    "status": status if status in {
                        "sent", "error", "scheduled", "draft", "pending"
                    } else "other",
                    "public_link": public_link,
                    "created_at": created[:25],
                })
        if dates and min(dates)[:19] < CUTOFF:
            exhaustive = True
            break
        if not page_info.get("hasNextPage"):
            exhaustive = True
            break
        nxt = str(page_info.get("endCursor") or "")
        if not nxt or nxt in seen_cursors:
            raise RuntimeError("BUFFER_CURSOR_LOOP_OR_MISSING")
        seen_cursors.add(nxt)
        cursor = nxt
    for ref in sorted(matches):
        observations = matches[ref]
        print(json.dumps({
            "event": "CORTES_LEGACY_BUFFER_EXACT_MATCH",
            "network": service, "record_ref": ref,
            "post_count": len(observations),
            "posts": observations,
        }, separators=(",", ":")), flush=True)
    print(json.dumps({
        "event": "CORTES_LEGACY_BUFFER_CENSUS",
        "network": service,
        "posts_scanned": count,
        "historical_window_complete": exhaustive,
        "exact_matches": sum(bool(x) for x in matches.values()),
        "unmatched": sum(not x for x in matches.values()),
        "no_posts_created": True,
    }, separators=(",", ":")), flush=True)
    if not exhaustive:
        raise RuntimeError("BUFFER_HISTORY_WINDOW_INCOMPLETE")


def main():
    orgs = read_organizations()
    for service, organization_id in orgs.items():
        read_channel(service, organization_id)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Never disclose raw Buffer error messages or identity data.
        print("CORTES_LEGACY_READBACK_BLOCKED=" + type(error).__name__, flush=True)
        raise SystemExit(3)
