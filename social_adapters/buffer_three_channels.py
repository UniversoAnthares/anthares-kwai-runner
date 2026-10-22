#!/usr/bin/env python3
"""CORTES Buffer adapter for Instagram, Pinterest and LinkedIn.

A Buffer API credential is injected securely by the Bitwarden GitHub action.
This module does not claim Neon jobs, schedule recurring jobs or confirm posts.
Writes are impossible unless ANTHARES_SOCIAL_COMMIT=1 and a real channel ID is
explicitly pinned. Buffer queue acceptance is NOT proof of social publication.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from anthares_publisher.editorial import branded_title, add_site_to_keywords

ENDPOINT = "https://api.buffer.com"
SERVICES = ("instagram", "pinterest", "linkedin")
LABEL = "Universo Anthares"
LINKEDIN_COMPANY = "145345334"
PINNED_CHANNELS = {
    "instagram": ("6ad8a3c3778b240e2f799ec8", "instagram.com", "/universoanthares"),
    "pinterest": ("6ad8a46d778b240e2f79a40f", "pinterest.com", "/lucasyahn"),
    "linkedin": ("6ad8a372778b240e2f799c72", "linkedin.com", "/company/" + LINKEDIN_COMPANY),
}

# Identified from the actual public Pinterest board created by the account owner.
# Board resource is authoritative even when Buffer's metadata GraphQL returns 500.
PINTEREST_PUBLIC_BOARD_ID = "819514532133906920"
PINTEREST_PUBLIC_BOARD_URL = "https://br.pinterest.com/lucasyahn/universo-anthares-v%C3%ADdeos/"


class BufferBlocked(RuntimeError):
    pass


def api(query: str, token: str | None = None) -> dict:
    secret = (token or os.getenv("BUFFER_API_KEY") or "").strip()
    if not secret:
        raise BufferBlocked("BUFFER_API_KEY_MISSING")
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({"query": query}, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Authorization": "Bearer " + secret, "Content-Type": "application/json",
                 "Accept": "application/json", "User-Agent": "AntharesBufferCortes/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        raise BufferBlocked("BUFFER_HTTP_" + str(exc.code)) from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise BufferBlocked("BUFFER_RESPONSE_UNCERTAIN") from None
    if not isinstance(result, dict) or result.get("errors") or not isinstance(result.get("data"), dict):
        raise BufferBlocked("BUFFER_GRAPHQL_OR_DATA_ERROR")
    return result["data"]


def channels(token: str | None = None) -> list[dict]:
    account = api("query { account { organizations { id name } } }", token).get("account") or {}
    output = []
    for organization in account.get("organizations") or []:
        org_id = str(organization.get("id") or "")
        if not org_id:
            continue
        query = ("query { channels(input: { organizationId: " + json.dumps(org_id) +
                 " }) { id name displayName service externalLink } }")
        output.extend(api(query, token).get("channels") or [])
    return output



def historical_pinterest_boards(token: str | None = None) -> list[dict]:
    """Recover owned board ID from this channel's verified sent Buffer Pins."""
    orgs=(api("query { account { organizations { id } } }",token).get("account") or {}).get("organizations") or []
    found={}
    channel_id=PINNED_CHANNELS["pinterest"][0]
    for org in orgs:
        oid=str(org.get("id") or "")
        if not oid:continue
        q=('query CortesHistoricalPins { posts(first: 30, input: { organizationId: '+
           json.dumps(oid)+', filter: {status: [sent], channelIds: ['+
           json.dumps(channel_id)+']} }) { edges { node {channelId metadata {'+
           ' ... on PinterestPostMetadata { board {serviceId name url} } } } } } }')
        result=api(q,token).get("posts") or {}
        for edge in result.get("edges") or []:
            row=edge.get("node") or {}
            if row.get("channelId")!=channel_id:continue
            board=(row.get("metadata") or {}).get("board") or {}
            sid=str(board.get("serviceId") or "")
            if sid:
                found[sid]={"serviceId":sid,"name":str(board.get("name") or ""),
                            "url":str(board.get("url") or "")}
    return list(found.values())


def pinterest_boards(token: str | None = None) -> list[dict]:
    """Read only Pinterest board IDs from the authenticated Buffer channel."""
    channel_id = PINNED_CHANNELS["pinterest"][0]
    query = ("query CortesPinterestBoards { channel(input: { id: " +
             json.dumps(channel_id) +
             " }) { id metadata { ... on PinterestMetadata { boards "
             "{ serviceId } } } }")
    entry = api(query, token).get("channel") or {}
    if entry.get("id") != channel_id:
        raise BufferBlocked("BUFFER_PINTEREST_CHANNEL_MISMATCH")
    metadata = entry.get("metadata") or {}
    rows = metadata.get("boards") or []
    if not isinstance(rows, list):
        raise BufferBlocked("BUFFER_PINTEREST_BOARD_RESPONSE_INVALID")
    clean = []
    for row in rows:
        sid = str(row.get("serviceId") or "").strip()
        if sid:
            clean.append({"serviceId": sid, "name": str(row.get("name") or ""),
                          "url": str(row.get("url") or "")})
    return clean


def select_pinterest_board(boards: list[dict], explicit: str = "") -> str:
    """No guessing across ambiguous boards; choose explicit or sole safe board."""
    if explicit:
        if any(str(row.get("serviceId")) == explicit for row in boards):
            return explicit
        raise BufferBlocked("PINTEREST_SELECTED_BOARD_NOT_OWNED_BY_ACCOUNT")
    if len(boards) == 1:
        return str(boards[0]["serviceId"])
    preferred = [row for row in boards if
                 str(row.get("name") or "").casefold() in
                 ("universo anthares", "cortes universo anthares")]
    if len(preferred) == 1:
        return str(preferred[0]["serviceId"])
    raise BufferBlocked("PINTEREST_BOARD_SELECTION_REQUIRED")

def validate_channel(platform: str, channel_id: str, available: list[dict]) -> dict:
    if platform not in SERVICES:
        raise BufferBlocked("UNSUPPORTED_PLATFORM")
    if not channel_id:
        raise BufferBlocked("BUFFER_CHANNEL_ID_REQUIRED")
    if channel_id != PINNED_CHANNELS[platform][0]:
        raise BufferBlocked("BUFFER_CHANNEL_ID_NOT_PINNED")
    exact = [x for x in available if str(x.get("id") or "") == channel_id]
    if len(exact) != 1:
        raise BufferBlocked("BUFFER_CHANNEL_NOT_FOUND_OR_AMBIGUOUS")
    entry = exact[0]
    service = str(entry.get("service") or "").lower()
    if service != platform:
        raise BufferBlocked("BUFFER_SERVICE_MISMATCH")
    if entry.get("isQueuePaused") or entry.get("isLocked") or entry.get("isDisconnected"):
        raise BufferBlocked("BUFFER_CHANNEL_UNAVAILABLE")
    name = " ".join(str(entry.get("displayName") or entry.get("name") or "").casefold().split())
    # Names must be verified with the connected social account. Do not match
    # a personal LinkedIn profile when the page is the required target.
    expected_name = {"instagram": "universoanthares", "pinterest": "lucasyahn", "linkedin": LABEL.casefold()}[platform]
    if name != expected_name:
        raise BufferBlocked("BUFFER_SOCIAL_ACCOUNT_NAME_UNVERIFIED")
    url = str(entry.get("externalLink") or "").strip()
    uri = urllib.parse.urlparse(url)
    expected_host, expected_path = PINNED_CHANNELS[platform][1:]
    if (uri.scheme != "https" or (uri.hostname or "").lower().removeprefix("www.") != expected_host
            or uri.path.rstrip("/").casefold() != expected_path.casefold()
            or uri.username or uri.password or uri.port):
        raise BufferBlocked("BUFFER_SOCIAL_ACCOUNT_URL_UNVERIFIED")
    return entry


def verified_public_pinterest_board() -> str:
    """Read-only confirmation that the exact owned board ID is still public.

    Pinterest's URL slug is not an API board identifier. Require the numeric
    ID to appear on the exact public board page; never infer an arbitrary ID.
    """
    request = urllib.request.Request(
        PINTEREST_PUBLIC_BOARD_URL,
        headers={"User-Agent": "Mozilla/5.0 AntharesPinterestBoardVerifier/1.0",
                 "Accept": "text/html"},
    )
    try:
        with urllib.request.urlopen(request, timeout=18) as response:
            if response.status != 200:
                raise BufferBlocked("PINTEREST_PUBLIC_BOARD_UNAVAILABLE")
            page = response.read(2_000_000).decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, TimeoutError) as exc:
        raise BufferBlocked("PINTEREST_PUBLIC_BOARD_UNAVAILABLE") from None
    if (PINTEREST_PUBLIC_BOARD_ID not in page
            or "universo-anthares-v" not in page.lower()
            or "lucasyahn" not in page.lower()):
        raise BufferBlocked("PINTEREST_PUBLIC_BOARD_OWNERSHIP_UNVERIFIED")
    return PINTEREST_PUBLIC_BOARD_ID


def resolve_pinterest_board(channel_id: str, *, token: str | None = None) -> str:
    """Select only a Pinterest board returned by the connected account."""
    if channel_id != PINNED_CHANNELS["pinterest"][0]:
        raise BufferBlocked("PINTEREST_CHANNEL_ID_NOT_PINNED")
    query = ('query { channel(input: { id: ' + json.dumps(channel_id) +
             ' }) { metadata { ... on PinterestMetadata { boards { serviceId name url } } } } }')
    try:
        details = api(query, token).get("channel") or {}
    except BufferBlocked as exc:
        if str(exc) not in ("BUFFER_HTTP_500","BUFFER_GRAPHQL_OR_DATA_ERROR"):
            raise
        # Read-only fallback: posts previously sent by the same pinned channel.
        # Newly created boards have no sent Pins yet. Validate the actual
        # public owned board, whose stable ID was recovered from Pinterest.
        explicit = os.getenv("BUFFER_PINTEREST_BOARD_ID", "").strip()
        if explicit and explicit != PINTEREST_PUBLIC_BOARD_ID:
            raise BufferBlocked("PINTEREST_BOARD_ENV_MISMATCH")
        return verified_public_pinterest_board()
    metadata = details.get("metadata") or {}
    boards = metadata.get("boards") or []
    if not isinstance(boards, list):
        raise BufferBlocked("PINTEREST_BOARD_LIST_INVALID")
    if len(boards) == 0:
        return verified_public_pinterest_board()
    pinned = os.getenv("BUFFER_PINTEREST_BOARD_ID", "").strip() or PINTEREST_PUBLIC_BOARD_ID
    if pinned != PINTEREST_PUBLIC_BOARD_ID:
        raise BufferBlocked("PINTEREST_BOARD_ENV_MISMATCH")
    matches = [board for board in boards
               if str(board.get("serviceId") or "") == pinned]
    if len(matches) != 1 or not str(matches[0].get("serviceId") or "").strip():
        raise BufferBlocked("PINTEREST_BOARD_NOT_VERIFIED")
    link = urllib.parse.urlparse(str(matches[0].get("url") or ""))
    if link.scheme != "https" or (link.hostname or "").lower().removeprefix("www.") not in ("pinterest.com", "br.pinterest.com"):
        raise BufferBlocked("PINTEREST_BOARD_URL_UNVERIFIED")
    return str(matches[0]["serviceId"])


def prepare(payload: dict) -> dict:
    platform = str(payload.get("platform") or "").lower()
    if platform not in SERVICES:
        raise BufferBlocked("UNSUPPORTED_PLATFORM")
    uri = urllib.parse.urlparse(str(payload.get("media_url") or payload.get("video_url") or ""))
    if (uri.scheme != "https" or uri.hostname not in ("anthares.us", "www.anthares.us")
            or uri.username or uri.password or not uri.path.lower().endswith(".mp4")):
        raise BufferBlocked("MASTER_MP4_URL_INVALID")
    title = str(payload.get("title") or payload.get("video_title") or "").strip()
    if not title:
        raise BufferBlocked("TITLE_MISSING")
    if payload.get("duration_seconds") is not None:
        try:
            duration = float(payload["duration_seconds"])
        except (ValueError, TypeError):
            raise BufferBlocked("DURATION_INVALID")
        if not 30 <= duration <= 90:
            raise BufferBlocked("DURATION_OUT_OF_SHORT_RANGE")
    if platform == "linkedin":
        from anthares_publisher.linkedin_editorial import linkedin_caption
        text = linkedin_caption(title, str(payload.get("description") or ""))
    else:
        text = add_site_to_keywords(branded_title(title) + "\n" + str(payload.get("description") or "").strip())
    if len(text) > 2200:
        raise BufferBlocked("CAPTION_TOO_LONG_REQUIRES_EDITORIAL_TRUNCATION")
    return {"platform": platform, "media_url": uri.geturl(), "caption": text,
            "pin_title": branded_title(title, limit=100)}


def trusted_instagram_one_time_runner() -> bool:
    """Narrow, temporary, owner-authorized emergency route for today's Buffer posts."""
    return (os.getenv("CORTES_INSTAGRAM_ONETIME_SELFHOSTED") == "1"
            and os.getenv("GITHUB_ACTIONS") == "true"
            and os.getenv("RUNNER_ENVIRONMENT") == "self-hosted"
            and os.getenv("RUNNER_OS") == "Windows"
            and os.getenv("GITHUB_REPOSITORY") == "UniversoAnthares/anthares-kwai-runner"
            and os.getenv("GITHUB_REF") == "refs/heads/main"
            and ((os.getenv("RUNNER_NAME") == "anthares-instagram-once-20261021"
                  and os.getenv("GITHUB_WORKFLOW_REF", "").endswith(
                      "/.github/workflows/cortes-buffer-instagram-cloud.yml@refs/heads/main"))
                 or (os.getenv("RUNNER_NAME") in ("anthares-instagram-fallback-20261021", "Anthares-TikTok-Lucas4-Windows-HA")
                     and os.getenv("GITHUB_WORKFLOW_REF", "").endswith(
                         "/.github/workflows/cortes-buffer-instagram-windows-fallback.yml@refs/heads/main"))))


def schedule(payload: dict, *, token: str | None = None, validated_channels: list[dict] | None = None) -> dict:
    post = prepare(payload)
    if os.getenv("ANTHARES_SOCIAL_COMMIT", "") != "1":
        return {"status": "DRY_RUN", **post}
    # Require a GitHub-hosted Linux Actions runner. Never publish from the
    # owner's PC, Anthares Remote, or a self-hosted GitHub runner.
    if (os.getenv("GITHUB_ACTIONS") != "true"
            or os.getenv("RUNNER_ENVIRONMENT") != "github-hosted"
            or os.getenv("RUNNER_OS") != "Linux") and not trusted_instagram_one_time_runner():
        raise BufferBlocked("BUFFER_CLOUD_HOSTED_RUNNER_REQUIRED")
    platform = post["platform"]
    channel_id = str(os.getenv("BUFFER_" + platform.upper() + "_CHANNEL_ID") or "").strip()
    # An authenticated read-only channel preflight may be reused by a fenced
    # publisher; avoid doubling Buffer API reads under HTTP 429 pressure.
    validate_channel(platform, channel_id, channels(token) if validated_channels is None else validated_channels)
    # Explicit Reel and Pinterest board metadata are mandatory. Never fall back
    # to a generic Instagram post or an arbitrary Pinterest board.
    # shareNow is an official Buffer mode: no queue slot and no spill into tomorrow.
    # This does not increase LinkedIn's real account/API posting allowance.
    if payload.get("same_day") is True:
        if platform not in ("linkedin","instagram"):
            raise BufferBlocked("SAME_DAY_IMMEDIATE_LINKEDIN_ONLY")
        mode = "shareNow"
    else:
        mode = "addToQueue"
    metadata = ""
    if platform == "instagram":
        metadata = "metadata: { instagram: { type: reel, shouldShareToFeed: true } }"
    elif platform == "pinterest":
        board_id = resolve_pinterest_board(channel_id, token=token)
        title = branded_title(str(payload.get("title") or payload.get("video_title") or ""), limit=100)
        metadata = ('metadata: { pinterest: { boardServiceId: ' + json.dumps(board_id) +
                    ', title: ' + json.dumps(title, ensure_ascii=False) +
                    ', url: "https://www.anthares.us" } }')
    mutation = """mutation CortesBufferVideo {
      createPost(input: {
        text: CAPTION
        channelId: CHANNEL
        schedulingType: automatic
        mode: SHARE_MODE
        METADATA
        assets: [{ video: { url: MEDIA, metadata: { thumbnailOffset: 2000 } } }]
      }) {
        ... on PostActionSuccess { post { id } }
        ... on MutationError { message }
      }
    }"""
    mutation = (mutation.replace("CAPTION", json.dumps(post["caption"], ensure_ascii=False))
               .replace("CHANNEL", json.dumps(channel_id))
               .replace("MEDIA", json.dumps(post["media_url"]))
               .replace("METADATA", metadata)
               .replace("SHARE_MODE", mode))
    result = api(mutation, token).get("createPost") or {}
    if not result.get("post") and isinstance(result.get("message"), str):
        msg = result["message"].lower()
        label = next((key for key, indicators in {
            "BOARD": ("board", "pasta"),
            "MEDIA": ("video", "media", "asset", "thumbnail"),
            "PERMISSION": ("permission", "access", "authorize", "scope", "connect"),
            "QUOTA": ("quota", "limit", "queue", "plan"),
            "METADATA": ("metadata", "pinterest", "title", "invalid"),
        }.items() if any(term in msg for term in indicators)), "UNCLASSIFIED")
        raise BufferBlocked("BUFFER_MUTATION_REJECTED_" + label)
    identifier = str((result.get("post") or {}).get("id") or "")
    if not identifier:
        raise BufferBlocked("BUFFER_SCHEDULE_REJECTED_OR_UNCERTAIN")
    return {"status": "SCHEDULED_IN_BUFFER", "platform": platform,
            "remote_id": identifier, "confirmed_on_social_network": False}


def main() -> int:
    try:
        mode = sys.argv[1] if len(sys.argv) > 1 else "dry-run"
        if mode == "list":
            data = channels()
            print(json.dumps([{k: c.get(k) for k in ("id","name","service","displayName","isQueuePaused","externalLink","type","isDisconnected","isLocked")} for c in data], ensure_ascii=False))
            return 0
        if mode not in ("dry-run", "schedule"):
            raise BufferBlocked("INVALID_MODE")
        payload = json.load(sys.stdin)
        if mode == "dry-run":
            os.environ["ANTHARES_SOCIAL_COMMIT"] = "0"
        result = schedule(payload)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except BufferBlocked as error:
        print(json.dumps({"status": "BLOCKED", "reason": str(error)}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
