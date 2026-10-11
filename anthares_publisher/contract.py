#!/usr/bin/env python3
"""Safety contract joining Anthares identity proof to publisher execution."""
from dataclasses import dataclass
from urllib.parse import unquote, urlsplit


@dataclass(frozen=True)
class IdentityProof:
    platform: str
    expected_account: str
    observed_account: str
    verified: bool
    session_fingerprint: str


@dataclass(frozen=True)
class PublicationEvidence:
    platform: str
    account: str
    external_id: str
    public_url: str


PLATFORM_DOMAINS = {
    "kwai": {"kwai.com", "www.kwai.com", "s.kwai.app", "www.kwai.app"},
    "tiktok": {"tiktok.com", "www.tiktok.com", "vm.tiktok.com"},
    "x": {"x.com", "www.x.com", "twitter.com", "www.twitter.com"},
    "instagram": {"instagram.com", "www.instagram.com"},
    "facebook": {"facebook.com", "www.facebook.com", "m.facebook.com"},
    "discord": {"discord.com", "www.discord.com"},
    "linkedin": {"linkedin.com", "www.linkedin.com"},
    "medium": {"medium.com", "www.medium.com"},
    "rumble": {"rumble.com", "www.rumble.com"},
    "odysee": {"odysee.com", "www.odysee.com"},
}


def normalize_account(value: str) -> str:
    return value.strip().lstrip("@").casefold()


def authorize(identity: IdentityProof, platform: str, account: str) -> None:
    if not identity.verified:
        raise PermissionError("identity proof is not verified")
    if identity.platform.casefold() != platform.casefold():
        raise PermissionError("identity platform mismatch")
    expected = normalize_account(account)
    if normalize_account(identity.expected_account) != expected:
        raise PermissionError("expected account mismatch")
    if normalize_account(identity.observed_account) != expected:
        raise PermissionError("observed account mismatch")
    if not identity.session_fingerprint:
        raise PermissionError("session fingerprint missing")


def _require_path_part(path_parts, value, message):
    if value not in path_parts:
        raise ValueError(message)


def validate_evidence(evidence: PublicationEvidence, platform: str, account: str) -> None:
    platform = platform.casefold()
    if evidence.platform.casefold() != platform:
        raise ValueError("publication platform mismatch")
    expected = normalize_account(account)
    if normalize_account(evidence.account) != expected:
        raise ValueError("publication account mismatch")
    external_id = evidence.external_id.strip()
    if not external_id:
        raise ValueError("external publication id missing")
    try:
        parsed = urlsplit(evidence.public_url)
        host = (parsed.hostname or "").lower()
        port = parsed.port
    except ValueError as exc:
        raise ValueError("invalid publication URL") from exc
    if (
        parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or port not in (None, 443)
        or host not in PLATFORM_DOMAINS.get(platform, set())
    ):
        raise ValueError("publication URL must use the target platform's HTTPS domain")

    decoded_path = unquote(parsed.path or "")
    path_parts = [part for part in decoded_path.split("/") if part]

    if platform == "x":
        _require_path_part(path_parts, external_id, "publication URL must identify the observed post")
        if "status" not in path_parts:
            raise ValueError("X publication URL must be a status URL")
        return

    if platform == "instagram":
        _require_path_part(path_parts, external_id, "publication URL must identify the observed post")
        if not ({"reel", "p"} & set(path_parts)):
            raise ValueError("Instagram publication URL must identify a reel or post")
        return

    if platform == "facebook":
        _require_path_part(path_parts, external_id, "publication URL must identify the observed post")
        if "reel" not in path_parts:
            raise ValueError("Facebook publication URL must identify a reel")
        return

    if platform == "discord":
        _require_path_part(path_parts, external_id, "Discord URL must identify the observed message")
        if len(path_parts) < 4 or path_parts[0] != "channels":
            raise ValueError("Discord publication URL must identify a channel message")
        return

    if platform == "linkedin":
        markers = (f"urn:li:activity:{external_id}", f"activity-{external_id}")
        if external_id not in path_parts and not any(marker in decoded_path for marker in markers):
            raise ValueError("LinkedIn URL must identify the observed post")
        if "/feed/update/" not in decoded_path and "/posts/" not in decoded_path:
            raise ValueError("LinkedIn publication URL must identify a feed update or post")
        return

    if platform == "medium":
        _require_path_part(path_parts, external_id, "Medium URL must identify the observed story")
        if not path_parts or not path_parts[0].startswith("@"):
            raise ValueError("Medium publication URL must identify a personal story")
        return

    if platform == "rumble":
        _require_path_part(path_parts, external_id, "Rumble URL must identify the observed video")
        if not external_id.startswith("v") or not external_id.endswith(".html"):
            raise ValueError("Rumble publication URL must identify a video page")
        return

    if platform == "odysee":
        _require_path_part(path_parts, external_id, "Odysee URL must identify the observed publication")
        if not any(part.startswith("@") for part in path_parts):
            raise ValueError("Odysee publication URL must identify a channel publication")
        return

    _require_path_part(path_parts, external_id, "publication URL must identify the observed post")
