#!/usr/bin/env python3
"""Exclusive cloud relay with Hostinger lease and automatic failback.

Only runs after explicit authenticated workflow_dispatch and account approval.
Never prints RTMP destinations, private SSH data, or source-page contents.
"""
import os
import pathlib
import re
import signal
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit

from tiktok_restream_cloud_encoder import fetch_manifest, write_playlist, make_args

HOST_SCRIPT = '/home/u566597497/.anthares-tiktok-restream/cloud-failover.py'
ORIGIN = '/home/u566597497/.anthares-tiktok-restream/program-origin-epoch'
MAX_RUNTIME = 20520
stop_requested = False


def stop_handler(sig, frame):
    global stop_requested
    stop_requested = True


def ssh_argv(remote):
    port = os.environ['TIKTOK_SSH_PORT']
    key = os.environ['TIKTOK_SSH_KEY_FILE']
    host = os.environ['TIKTOK_SSH_HOST']
    user = os.environ['TIKTOK_SSH_USER']
    if not port.isdigit() or not re.match(r'^[A-Za-z0-9_.-]+$', host) or not re.match(r'^[A-Za-z0-9_-]+$', user):
        raise RuntimeError('invalid_ssh_bridge')
    return ['ssh', '-p', port, '-i', key, '-o', 'BatchMode=yes',
            '-o', 'IdentitiesOnly=yes', '-o', 'ConnectTimeout=12',
            '-o', 'StrictHostKeyChecking=accept-new',
            user + '@' + host, remote]


def remote(command, timeout=40):
    result = subprocess.run(ssh_argv(command), stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, universal_newlines=True,
                            timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError('cloud_host_command_failed')
    return result.stdout.strip()


def gate():
    if os.environ.get('RESTREAM_TIKTOK_CHANNEL_AUTHORIZED') != 'true':
        raise RuntimeError('restream_channel_not_authorized')
    if os.environ.get('RESTREAM_PRERECORDED_APPROVED') != 'true':
        raise RuntimeError('prerecorded_content_not_approved')
    url = os.environ.get('RESTREAM_ENCODER_RTMP_DESTINATION', '')
    u = urlsplit(url)
    if u.scheme not in ('rtmp','rtmps') or u.hostname != 'live.restream.io' or not u.path.startswith('/live/') or u.username or u.password:
        raise RuntimeError('invalid_restream_ingest')
    n = os.environ.get('GITHUB_RUN_ID', '')
    if not re.match(r'^[0-9]{8,20}$', n):
        raise RuntimeError('invalid_run_identity')
    return url, n


def main():
    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)
    url, owner = gate()
    requested = int(os.environ.get('STREAM_SECONDS', '19800'))
    if not 90 <= requested <= MAX_RUNTIME:
        raise RuntimeError('duration_out_of_bounds')
    origin = remote('cat ' + ORIGIN)
    if not re.match(r'^[0-9]{10}$', origin):
        raise RuntimeError('invalid_program_clock')
    origin = int(origin)
    with tempfile.TemporaryDirectory(prefix='anthares-cloud-relay-') as base:
        root = pathlib.Path(base)
        now = int(time.time())
        phase = (now-origin)%21600
        remaining = 21600-phase
        # End cleanly before the program's six-hour boundary.
        seconds = min(requested, remaining)
        if seconds < 90:
            raise RuntimeError('source_window_ending_soon')
        print('CLOUD_PROGRAM_POSITION={} WINDOW_SECONDS={}'.format(phase, seconds), flush=True)
        parts = fetch_manifest()
        manifest = root/'source.m3u8'
        residual = write_playlist(parts, phase, manifest)
        progress = root/'ffmpeg.progress'
        cmd = make_args(manifest, residual, seconds, url)
        pos = cmd.index('pipe:1')
        cmd[pos] = str(progress)
        # Mandatory source proof before touching the running Hostinger encoder.
        dry = make_args(manifest, residual, 8, os.devnull)
        proof = subprocess.run(dry, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               timeout=55, universal_newlines=True)
        if proof.returncode or 'progress=end' not in proof.stdout:
            raise RuntimeError('cloud_encoder_dry_run_failed')
        print('CLOUD_READY_TO_CLAIM=1', flush=True)
        claimed = False
        proc = None
        try:
            out = remote('python3 {} claim {}'.format(HOST_SCRIPT, owner), timeout=35)
            if 'CLOUD_CLAIM=PASS' not in out:
                raise RuntimeError('cloud_host_claim_not_confirmed')
            claimed = True
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    stdin=subprocess.DEVNULL, start_new_session=True)
            print('CLOUD_RELAY_STARTED=1', flush=True)
            began = time.monotonic()
            last_progress = began
            last_size = -1
            failures = 0
            while proc.poll() is None and not stop_requested:
                time.sleep(10)
                if progress.exists():
                    value = progress.stat().st_size
                    if value > last_size:
                        last_size = value
                        last_progress = time.monotonic()
                if time.monotonic()-last_progress > 130:
                    raise RuntimeError('cloud_relay_progress_stalled')
                # The lease must be renewed before its 210-second expiry.
                if int(time.monotonic()-began) % 40 < 11:
                    try:
                        receipt = remote('python3 {} heartbeat {}'.format(HOST_SCRIPT, owner),timeout=26)
                        if 'CLOUD_HEARTBEAT=PASS' not in receipt:
                            raise RuntimeError('unconfirmed_heartbeat')
                        failures = 0
                    except Exception:
                        failures += 1
                        if failures >= 2:
                            raise RuntimeError('cloud_host_heartbeat_lost')
                if int(time.monotonic()-began)%3600 < 11:
                    print('CLOUD_RELAY_RUNNING=1 elapsed_minutes={}'.format(int((time.monotonic()-began)//60)),flush=True)
            rc=proc.poll()
            if stop_requested:
                raise RuntimeError('cloud_relay_cancelled')
            if rc != 0:
                raise RuntimeError('cloud_relay_ffmpeg_exited')
            print('CLOUD_RELAY_COMPLETED=1 elapsed_minutes={}'.format(int((time.monotonic()-began)//60)),flush=True)
        finally:
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=9)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
            if claimed:
                try:
                    outcome=remote('python3 {} release {}'.format(HOST_SCRIPT, owner),timeout=42)
                    print('CLOUD_HOST_FAILBACK_CONFIRMED={}'.format(int('CLOUD_RELEASE=PASS' in outcome)),flush=True)
                except Exception:
                    # Lease expiry is independently polled by both Hostinger and WP cron.
                    print('CLOUD_HOST_FAILBACK_PENDING_LEASE_EXPIRY=1',flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('CLOUD_RELAY_STATUS={}'.format(str(error)[:85].replace(' ','_')),flush=True)
        sys.exit(1)
