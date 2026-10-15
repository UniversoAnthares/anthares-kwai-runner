#!/usr/bin/env python3
"""Legacy import compatibility only; Render is permanently retired.

No Render API, host, credential or runtime is used here. The sole purpose of
this module is to migrate old `persist_session_state` callers to the canonical
Anthares Browser runtime vault until the legacy import name is removed in the
retired-path cleanup phase.
"""
from __future__ import annotations

from tiktok_session_authority import persist_canonical_state


def persist_session_state(state: dict) -> bool:
    persist_canonical_state(state)
    return True
