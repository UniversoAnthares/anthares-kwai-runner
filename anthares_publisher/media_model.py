#!/usr/bin/env python3
"""Canonical Anthares media domain: Source -> Clip -> Publication.

This module is intentionally persistence-free and provider-neutral. Queue,
lease, dedupe, retry and reconciliation backends may change or fail over
without changing canonical media identity. Keeping this layer pure prevents
any infrastructure provider from becoming the domain authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

SHORT_PLATFORMS={"kwai","tiktok","instagram","pinterest","linkedin","threads"}
LONG_PLATFORMS={"youtube","facebook","x","bilibili","odysee","rumble","bluesky","reddit"}
ALL_PLATFORMS=SHORT_PLATFORMS|LONG_PLATFORMS
DAILY_LIMITS={
    "kwai":100,"tiktok":100,"instagram":20,"pinterest":20,"linkedin":20,"threads":100,
    "youtube":3,"facebook":10,"x":10,"bilibili":10,"odysee":10,"rumble":10,
    "bluesky":10,"reddit":10,
}


def _stable_id(*parts):
    return hashlib.sha256("\n".join(map(str,parts)).encode()).hexdigest()

def normalize_platform(value):
    platform=str(value).strip().casefold()
    if platform=="twitter": platform="x"
    if platform not in ALL_PLATFORMS: raise ValueError(f"unsupported platform: {platform}")
    return platform

def normalize_account(value):
    account=str(value).strip().lstrip("@").casefold()
    if not account: raise ValueError("account_id is required")
    return account

def _sha256(value,name):
    digest=str(value).strip().casefold()
    if len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError(f"{name} must be a 64-character sha256 hex digest")
    return digest

@dataclass(frozen=True)
class Source:
    source_id:str
    uri:str|None=None
    source_sha256:str|None=None

    def __post_init__(self):
        source_id=str(self.source_id).strip()
        if not source_id: raise ValueError("source_id is required")
        object.__setattr__(self,"source_id",source_id)
        if self.source_sha256 is not None:
            object.__setattr__(self,"source_sha256",_sha256(self.source_sha256,"source_sha256"))

@dataclass(frozen=True)
class Clip:
    source_id:str
    start_ms:int
    end_ms:int
    duration_class:str
    content_sha256:str
    storage_uri:str|None=None
    master_id:str|None=None

    def __post_init__(self):
        source_id=str(self.source_id).strip(); start=int(self.start_ms); end=int(self.end_ms)
        duration_class=str(self.duration_class).strip().casefold()
        if not source_id: raise ValueError("source_id is required")
        if start<0 or end<=start: raise ValueError("invalid clip interval")
        seconds=(end-start)/1000.0
        if duration_class=="short" and not 30<=seconds<=90: raise ValueError("short clip must be 30-90 seconds")
        if duration_class=="long" and not 300<=seconds<=840: raise ValueError("long clip must be 5-14 minutes")
        if duration_class not in {"short","long"}: raise ValueError("duration_class must be short or long")
        digest=_sha256(self.content_sha256,"content_sha256")
        master=str(self.master_id or digest).strip()
        if not master: raise ValueError("master_id is required")
        object.__setattr__(self,"source_id",source_id); object.__setattr__(self,"start_ms",start); object.__setattr__(self,"end_ms",end)
        object.__setattr__(self,"duration_class",duration_class); object.__setattr__(self,"content_sha256",digest); object.__setattr__(self,"master_id",master)

    @property
    def clip_id(self): return _stable_id(self.source_id,self.start_ms,self.end_ms,self.duration_class,self.master_id)

@dataclass(frozen=True)
class Publication:
    clip:Clip
    platform:str
    account_id:str

    def __post_init__(self):
        platform=normalize_platform(self.platform); account=normalize_account(self.account_id)
        if platform in SHORT_PLATFORMS and self.clip.duration_class!="short": raise ValueError("short-form platform requires short master")
        if platform in LONG_PLATFORMS and self.clip.duration_class!="long": raise ValueError("long-form platform requires long master")
        object.__setattr__(self,"platform",platform); object.__setattr__(self,"account_id",account)

    @property
    def publication_id(self): return _stable_id(self.clip.master_id,self.platform,self.account_id)
    @property
    def target_key(self): return f"{self.platform}:{self.account_id}"
    @property
    def daily_limit(self): return DAILY_LIMITS[self.platform]
    @property
    def dedupe_key(self): return _stable_id(self.clip.master_id,self.platform,self.account_id)

    def control_payload(self):
        """Canonical enqueue payload accepted by any compatible control backend."""
        return {
            "id":self.publication_id,
            "platform":self.platform,
            "account_id":self.account_id,
            "target_key":self.target_key,
            "master_id":self.clip.master_id,
            "dedupe_key":self.dedupe_key,
            "media_sha256":self.clip.content_sha256,
            "source_id":self.clip.source_id,
            "source_start":self.clip.start_ms,
            "source_end":self.clip.end_ms,
            "duration_class":self.clip.duration_class,
        }

def source_safe_to_delete(processing_complete,publications):
    """Source bytes may be deleted only after every planned target is confirmed."""
    statuses=list(publications)
    return bool(processing_complete and statuses and all(str(s).casefold()=="confirmed" for s in statuses))