#!/usr/bin/env python3
"""Safety contract joining Anthares Mobile identity proof to Publisher execution."""
from dataclasses import dataclass
from typing import Optional

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


def authorize(identity: IdentityProof, platform: str, account: str) -> None:
    if not identity.verified:
        raise PermissionError("identity proof is not verified")
    if identity.platform.casefold()!=platform.casefold():
        raise PermissionError("identity platform mismatch")
    expected=account.strip().lstrip('@').casefold()
    if identity.expected_account.strip().lstrip('@').casefold()!=expected:
        raise PermissionError("expected account mismatch")
    if identity.observed_account.strip().lstrip('@').casefold()!=expected:
        raise PermissionError("observed account mismatch")
    if not identity.session_fingerprint:
        raise PermissionError("session fingerprint missing")


def validate_evidence(evidence: PublicationEvidence, platform: str, account: str) -> None:
    if evidence.platform.casefold()!=platform.casefold():
        raise ValueError("publication platform mismatch")
    expected=account.strip().lstrip('@').casefold()
    if evidence.account.strip().lstrip('@').casefold()!=expected:
        raise ValueError("publication account mismatch")
    if not evidence.external_id.strip():
        raise ValueError("external publication id missing")
    if not evidence.public_url.startswith(('https://','http://')):
        raise ValueError("public publication URL missing")
