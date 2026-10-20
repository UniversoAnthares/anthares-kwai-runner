"""Static regression guards for Anthares Remote control-plane routes."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_android_backup_uses_same_device_api_as_primary():
    src = (ROOT / "android-agent/app/src/main/java/us/anthares/agent/RemoteControlLoop.java").read_text(encoding="utf-8")
    assert 'BACKUP="https://anthares-remote-secondary.vercel.app"' in src
    assert 'BACKUP="https://anthares-ara-vercel-reserve.vercel.app"' not in src


def test_legacy_vercel_probe_uses_healthz_contract():
    path = ROOT / ".github/workflows/ara-vercel-reserve-probe.yml"
    src = path.read_text(encoding="utf-8")
    assert "'/healthz'" in src
    assert 'test "$code" = "200"' in src
    assert '"/health"' not in src


def test_post_cutover_probe_accepts_supported_oauth_identity_modes():
    src = (ROOT / ".github/workflows/ara-post-cutover-probe.yml").read_text(encoding="utf-8")
    assert 'anthares-ara-vercel-reserve.vercel.app/healthz' in src
    assert 'github_owner_identity|email_otp' in src


def test_control_probe_is_authenticated_read_only():
    src = (ROOT / "anthares-remote-agent/windows/probe-vercel-control.ps1").read_text(encoding="utf-8")
    assert "/v1/device/auth-check" in src
    assert 'remote-secondary.vercel.app' in src
    assert "/v1/device/heartbeat" not in src
    assert re.search(r"\$healthy\s*-ge\s*1", src)
