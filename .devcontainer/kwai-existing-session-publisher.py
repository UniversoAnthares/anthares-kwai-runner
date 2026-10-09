#!/usr/bin/env python3
"""Publisher core for an already-open Kwai/Studio page.

The caller owns the browser/context. This module never launches a browser and never
reads/exports cookies, storage, tokens or screenshots. Publication is two-phase:
prepare_upload() may attach media/caption only after strict gates; publish_prepared()
requires the same gates plus an explicit final confirmation flag.
"""
import re
from pathlib import Path


def authorization(identity_verified, operational_create_surface):
    allowed = bool(identity_verified and operational_create_surface)
    return {
        "identity_verified": bool(identity_verified),
        "operational_create_surface": bool(operational_create_surface),
        "mutation_allowed": allowed,
        "publication_allowed": allowed,
    }


def require_authorization(identity_verified, operational_create_surface):
    gates = authorization(identity_verified, operational_create_surface)
    if not gates["mutation_allowed"]:
        raise PermissionError("identity_and_create_surface_required")
    return gates


async def prepare_upload(page, media_path, caption, *, identity_verified, operational_create_surface):
    """Attach media and optional caption to an existing page, but do not publish."""
    require_authorization(identity_verified, operational_create_surface)
    media = Path(media_path)
    if not media.is_file():
        raise FileNotFoundError(str(media))

    upload = page.locator("input[type=file]").first
    if await upload.count() < 1:
        raise RuntimeError("upload_input_not_found")
    await upload.set_input_files(str(media))

    caption_applied = False
    if caption:
        candidates = [
            page.locator("textarea").first,
            page.locator("[contenteditable=true]").first,
        ]
        for candidate in candidates:
            try:
                if await candidate.count() and await candidate.is_visible():
                    await candidate.fill(caption)
                    caption_applied = True
                    break
            except Exception:
                continue
    return {
        "prepared": True,
        "caption_applied": bool(caption_applied),
        "published": False,
    }


async def publish_prepared(page, *, identity_verified, operational_create_surface, final_confirmation):
    """Click the final publish control only with all independent gates asserted."""
    require_authorization(identity_verified, operational_create_surface)
    if not final_confirmation:
        raise PermissionError("explicit_final_confirmation_required")

    button = page.get_by_role("button", name=re.compile(r"^(Publish|Post|Publicar)$", re.I)).first
    if await button.count() < 1 or not await button.is_visible():
        raise RuntimeError("publish_control_not_found")
    await button.click()
    return {"publish_click_attempted": True}
