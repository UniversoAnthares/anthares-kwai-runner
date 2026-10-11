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
    path_parts = [part for part in unquote(parsed.path or "").split("/") if part]
    if external_id not in path_parts:
        raise ValueError("publication URL must identify the observed post")
    if platform == "x" and "status" not in path_parts:
        raise ValueError("X publication URL must be a status URL")
    if platform == "instagram" and not ({"reel", "p"} & set(path_parts)):
        raise ValueError("Instagram publication URL must identify a reel or post")
