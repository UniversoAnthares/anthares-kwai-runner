"""Browser UI publisher for personal X and Instagram accounts.

Requires Playwright and an authenticated, authorized persistent browser profile.
Never attempts to bypass authentication challenges or platform restrictions.
"""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

def publish(platform, video, caption, profile, commit=False):
    if platform not in ("x", "instagram"):
        raise ValueError("unsupported platform")
    if not Path(video).is_file():
        raise FileNotFoundError(video)
    if not commit:
        return {"status": "DRY_RUN", "platform": platform, "video": str(video)}
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(profile), headless=True, accept_downloads=False
        )
        page = context.new_page()
        try:
            if platform == "x":
                page.goto("https://x.com/compose/post", wait_until="domcontentloaded")
                page.get_by_role("textbox", name="Post text").fill(caption)
                page.locator('input[type="file"]').set_input_files(video)
                page.get_by_role("button", name="Post", exact=True).click()
            else:
                page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
                page.get_by_text("Create", exact=True).click()
                page.locator('input[type="file"]').set_input_files(video)
                page.get_by_role("button", name="Next").click()
                page.get_by_role("button", name="Next").click()
                page.locator('[role="textbox"]').last.fill(caption)
                page.get_by_role("button", name="Share").click()
            return {"status": "SUBMITTED_UNVERIFIED", "platform": platform}
        finally:
            context.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=["x", "instagram"], required=True)
    parser.add_argument("--video", required=True)
    parser.add_argument("--caption", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()
    print(json.dumps(publish(args.platform, args.video, args.caption, args.profile, args.commit)))
