#!/usr/bin/env python3
"""Read-only reconciliation for a TikTok publication already confirmed by Studio UI.

Never uploads or clicks Publish. It locates the exact Studio publication row and
uses its view/open action to recover the public video URL/ID.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

from tiktok_session_authority import load_canonical_state

VIDEO_RE = re.compile(r"https?://(?:www\.)?tiktok\.com/@([^/?#]+)/video/(\d+)", re.I)
ID_RE = re.compile(r"/video/(\d{8,})", re.I)
EXPECTED_ACCOUNT = os.getenv("EXPECTED_TIKTOK_USERNAME", "universo.anthares").strip().lstrip("@").casefold()
TARGET_TEXT = os.getenv("TIKTOK_RECONCILE_TEXT", "A Poetica de Aristoteles trecho").strip()
OUTPUT = Path(os.getenv("TIKTOK_RECONCILE_EVIDENCE", "/tmp/tiktok-reconcile-evidence.json"))


def extract_candidate(urls: list[str]) -> tuple[str, str] | None:
    for url in urls:
        m = VIDEO_RE.search(str(url))
        if m and m.group(1).casefold() == EXPECTED_ACCOUNT:
            return m.group(2), m.group(0)
    for url in urls:
        m = ID_RE.search(str(url))
        if m:
            return m.group(1), f"https://www.tiktok.com/@{EXPECTED_ACCOUNT}/video/{m.group(1)}"
    return None


def main() -> int:
    if not TARGET_TEXT:
        raise RuntimeError("reconcile target text missing")
    state, meta = load_canonical_state()
    observed_urls: list[str] = []
    row_snapshot: dict = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-dev-shm-usage", "--no-sandbox", "--disable-gpu"])
        ctx = browser.new_context(storage_state=state, viewport={"width": 1440, "height": 1000}, locale="pt-BR")
        page = ctx.new_page()
        try:
            for url in (
                "https://www.tiktok.com/tiktokstudio/content",
                "https://www.tiktok.com/tiktokstudio",
            ):
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    time.sleep(5)
                    if TARGET_TEXT.casefold() in page.locator("body").inner_text(timeout=5000).casefold():
                        break
                    pub = page.get_by_text("Publicações", exact=True)
                    if pub.count() and pub.first.is_visible(timeout=1000):
                        pub.first.click(timeout=5000)
                        time.sleep(5)
                        if TARGET_TEXT.casefold() in page.locator("body").inner_text(timeout=5000).casefold():
                            break
                except Exception:
                    continue
            body = page.locator("body").inner_text(timeout=5000)
            if TARGET_TEXT.casefold() not in body.casefold():
                raise RuntimeError("target publication row not found in TikTok Studio")

            target = page.get_by_text(re.compile(re.escape(TARGET_TEXT), re.I)).first
            if not target.count():
                raise RuntimeError("target publication text locator missing")
            row = target
            for _ in range(9):
                txt = row.inner_text(timeout=3000)
                buttons = row.locator("button").count()
                links = row.locator("a[href]").count()
                if TARGET_TEXT.casefold() in txt.casefold() and buttons >= 2 and len(txt) < 2500:
                    row_snapshot = {"text": txt[:1200], "buttons": buttons, "links": links}
                    break
                row = row.locator("xpath=..")
            else:
                raise RuntimeError("could not isolate exact Studio publication row")

            observed_urls.extend(row.locator("a[href]").evaluate_all("els => els.map(e => e.href)"))
            observed_urls.extend([str(pg.url) for pg in ctx.pages])
            candidate = extract_candidate(observed_urls)

            if not candidate:
                buttons = row.locator("button")
                click_order = [1, 2, 3]
                for index in click_order:
                    if index >= buttons.count():
                        continue
                    before_pages = set(id(pg) for pg in ctx.pages)
                    try:
                        buttons.nth(index).click(timeout=5000)
                        time.sleep(4)
                    except Exception:
                        continue
                    for pg in ctx.pages:
                        observed_urls.append(str(pg.url))
                        if id(pg) not in before_pages:
                            try:
                                pg.wait_for_load_state("domcontentloaded", timeout=15000)
                            except Exception:
                                pass
                            observed_urls.append(str(pg.url))
                    observed_urls.extend(page.locator("a[href]").evaluate_all("els => els.map(e => e.href)"))
                    candidate = extract_candidate(observed_urls)
                    if candidate:
                        break
                    # Close modal/menu side effects without navigating away when possible.
                    try:
                        page.keyboard.press("Escape")
                    except Exception:
                        pass
            if not candidate:
                html = page.content()
                for m in re.finditer(r"(?:https?:\\?/\\?/[^\"'<> ]+)?/video/(\d{8,})", html, re.I):
                    observed_urls.append(f"https://www.tiktok.com/@{EXPECTED_ACCOUNT}/video/{m.group(1)}")
                candidate = extract_candidate(observed_urls)
            if not candidate:
                raise RuntimeError("publication is visible in Studio but remote video ID/URL could not be extracted")

            remote_id, remote_url = candidate
            evidence = {
                "confirmed": True,
                "confirmation": "tiktok_studio_exact_row_reconciliation",
                "account": EXPECTED_ACCOUNT,
                "target_text": TARGET_TEXT,
                "remote_id": remote_id,
                "remote_url": remote_url,
                "studio_row": row_snapshot,
                "authority": meta.get("authority"),
                "authority_sha256": meta.get("ciphertext_sha256"),
                "reconciled_at": int(time.time()),
            }
            OUTPUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
            print("TIKTOK_UNCERTAIN_RECONCILED=1")
            print("REMOTE_ID=" + remote_id)
            print("REMOTE_URL=" + remote_url)
            return 0
        finally:
            ctx.close()
            browser.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("RECONCILE_ERROR=" + str(exc), file=sys.stderr, flush=True)
        raise
