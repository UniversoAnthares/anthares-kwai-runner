"""Safe contracts for persistent Anthares publishers.

The module stores and emits metadata only. Browser cookies, local storage, tokens,
passwords and session payloads are deliberately rejected.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable
from urllib.parse import urlparse

PLATFORMS = {"tiktok": "tiktok.com", "kwai": "kwai.com"}
SENSITIVE_PARTS = (
    "cookie",
    "password",
    "passwd",
    "token",
    "secret",
    "storage_state",
    "localstorage",
    "session_storage",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _parse_time(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError("timestamp_missing")
    raw = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise RuntimeError("timestamp_invalid") from exc
    if parsed.tzinfo is None:
        raise RuntimeError("timestamp_timezone_required")
    return parsed.astimezone(timezone.utc)


def _reject_sensitive(value, path: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            label = str(key).lower()
            if any(part in label for part in SENSITIVE_PARTS):
                raise RuntimeError(f"sensitive_field_rejected:{path}{key}")
            _reject_sensitive(child, f"{path}{key}.")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_sensitive(child, f"{path}{index}.")


@dataclass(frozen=True)
class ManagedProfileProof:
    provider: str
    profile_id: str
    platform: str
    account_handle: str
    checked_at: str
    authenticated: bool
    persistence_verified: bool

    @classmethod
    def from_mapping(cls, row: dict) -> "ManagedProfileProof":
        _reject_sensitive(row)
        platform = str(row.get("platform", "")).lower()
        if platform not in PLATFORMS:
            raise RuntimeError("managed_profile_platform_invalid")
        proof = cls(
            provider=str(row.get("provider", "")).strip(),
            profile_id=str(row.get("profile_id", "")).strip(),
            platform=platform,
            account_handle=str(row.get("account_handle", "")).strip(),
            checked_at=str(row.get("checked_at", "")).strip(),
            authenticated=row.get("authenticated") is True,
            persistence_verified=row.get("persistence_verified") is True,
        )
        if not proof.provider:
            raise RuntimeError("managed_profile_provider_missing")
        if not proof.profile_id:
            raise RuntimeError("managed_profile_id_missing")
        if not proof.account_handle:
            raise RuntimeError("managed_profile_account_missing")
        _parse_time(proof.checked_at)
        if not proof.authenticated:
            raise RuntimeError(f"managed_profile_not_authenticated:{platform}")
        if not proof.persistence_verified:
            raise RuntimeError(f"managed_profile_persistence_unverified:{platform}")
        return proof


def decode_managed_profiles(value: str | None) -> list[ManagedProfileProof]:
    if not value:
        raise RuntimeError("managed_profiles_missing")
    try:
        raw = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("managed_profiles_invalid_json") from exc
    rows = raw.get("profiles") if isinstance(raw, dict) else raw
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("managed_profiles_empty")
    proofs = [ManagedProfileProof.from_mapping(row) for row in rows if isinstance(row, dict)]
    if len(proofs) != len(rows):
        raise RuntimeError("managed_profiles_invalid_entry")
    seen = set()
    for proof in proofs:
        if proof.platform in seen:
            raise RuntimeError(f"managed_profile_duplicate:{proof.platform}")
        seen.add(proof.platform)
    return proofs


def require_platforms(proofs: Iterable[ManagedProfileProof], required: Iterable[str]) -> dict[str, ManagedProfileProof]:
    by_platform = {proof.platform: proof for proof in proofs}
    for platform in required:
        if platform not in PLATFORMS:
            raise RuntimeError(f"required_platform_invalid:{platform}")
        if platform not in by_platform:
            raise RuntimeError(f"managed_profile_missing:{platform}")
    return by_platform


@dataclass(frozen=True)
class PublishReceipt:
    platform: str
    provider: str
    profile_id: str
    account_handle: str
    post_id: str
    post_url: str
    published_at: str
    content_sha256: str
    identity_verified: bool
    publication_verified: bool

    @classmethod
    def from_mapping(cls, row: dict) -> "PublishReceipt":
        _reject_sensitive(row)
        platform = str(row.get("platform", "")).lower()
        if platform not in PLATFORMS:
            raise RuntimeError("receipt_platform_invalid")
        receipt = cls(
            platform=platform,
            provider=str(row.get("provider", "")).strip(),
            profile_id=str(row.get("profile_id", "")).strip(),
            account_handle=str(row.get("account_handle", "")).strip(),
            post_id=str(row.get("post_id", "")).strip(),
            post_url=str(row.get("post_url", "")).strip(),
            published_at=str(row.get("published_at", "")).strip(),
            content_sha256=str(row.get("content_sha256", "")).lower().strip(),
            identity_verified=row.get("identity_verified") is True,
            publication_verified=row.get("publication_verified") is True,
        )
        for field in ("provider", "profile_id", "account_handle", "post_id", "post_url"):
            if not getattr(receipt, field):
                raise RuntimeError(f"receipt_{field}_missing")
        parsed = urlparse(receipt.post_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise RuntimeError("receipt_post_url_invalid")
        _parse_time(receipt.published_at)
        if not _SHA256_RE.fullmatch(receipt.content_sha256):
            raise RuntimeError("receipt_content_sha256_invalid")
        if not receipt.identity_verified:
            raise RuntimeError("receipt_identity_unverified")
        if not receipt.publication_verified:
            raise RuntimeError("receipt_publication_unverified")
        return receipt

    @property
    def receipt_id(self) -> str:
        canonical = json.dumps(
            {
                "platform": self.platform,
                "provider": self.provider,
                "profile_id": self.profile_id,
                "account_handle": self.account_handle,
                "post_id": self.post_id,
                "post_url": self.post_url,
                "published_at": self.published_at,
                "content_sha256": self.content_sha256,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def public_dict(self) -> dict:
        row = asdict(self)
        row["receipt_id"] = self.receipt_id
        return row


def write_receipt(receipt: PublishReceipt, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(receipt.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(target)
    return target


def receipt_evidence(receipt: PublishReceipt) -> dict:
    return {
        "task": f"{receipt.platform}_publish_proof",
        "status": "verified",
        "source": receipt.post_url,
        "detail": f"receipt:{receipt.receipt_id}",
        "observed_at": receipt.published_at,
    }
