#!/usr/bin/env python3
"""Deterministic decision policy for Anthares execution failures.

This module answers one operational question: repair Anthares, migrate provider,
use an implementation agent, or require owner action.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Action(str, Enum):
    USE = "USE"
    REPAIR_ANTHARES = "REPAIR_ANTHARES"
    MIGRATE_PROVIDER = "MIGRATE_PROVIDER"
    USE_IMPLEMENTATION_AGENT = "USE_IMPLEMENTATION_AGENT"
    MANUAL_OWNER = "MANUAL_OWNER"
    FAIL_CLOSED = "FAIL_CLOSED"


RETIRED = {"render", "tinyfish", "circleci", "browserless"}
ANTHARES_COMPONENTS = {
    "anthares_remote",
    "anthares_browser",
    "anthares_reserva",
    "anthares_cloudflare",
    "anthares_control",
}
MANUAL_BOUNDARIES = {"mfa", "captcha", "account_authorization", "billing", "plan_change", "security_boundary"}
IMPLEMENTATION_WORK = {"code_change", "repository_refactor", "browser_workflow_build", "multi_step_implementation"}


@dataclass(frozen=True)
class Decision:
    action: Action
    reason: str
    retry_same_provider: bool = False


def decide(component: str, failure: str, quota_state: str = "UNKNOWN", agent_available: bool = False) -> Decision:
    component = component.strip().lower()
    failure = failure.strip().lower()
    quota_state = quota_state.strip().upper()

    if component in RETIRED:
        return Decision(Action.MIGRATE_PROVIDER, "retired_provider")
    if quota_state == "BLOCKED_QUOTA" or failure in {"quota", "quota_exceeded", "ci_quota_exceeded"}:
        return Decision(Action.MIGRATE_PROVIDER, "blocked_quota")
    if failure in MANUAL_BOUNDARIES:
        return Decision(Action.MANUAL_OWNER, failure)
    if component in ANTHARES_COMPONENTS and failure in {"down", "unhealthy", "timeout", "protocol", "state", "regression", "unknown_runtime"}:
        return Decision(Action.REPAIR_ANTHARES, "anthares_component_failure", retry_same_provider=True)
    if failure in IMPLEMENTATION_WORK and agent_available:
        return Decision(Action.USE_IMPLEMENTATION_AGENT, failure)
    if failure in {"provider_down", "unsupported_capability"}:
        return Decision(Action.MIGRATE_PROVIDER, failure)
    if failure in {"healthy", "ready"}:
        return Decision(Action.USE, failure, retry_same_provider=True)
    return Decision(Action.FAIL_CLOSED, "unclassified_failure")


def validate_surface(role: str, provider: str) -> bool:
    role = role.strip().lower()
    provider = provider.strip().lower()
    if role == "remote_control":
        return provider == "anthares_remote"
    if role == "browser":
        return provider == "anthares_browser"
    return provider not in RETIRED
