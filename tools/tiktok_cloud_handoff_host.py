#!/usr/bin/env python3
"""Hostinger/TikTok cloud relay handoff. No credentials or account state stored."""
import fcntl
import os
import pathlib
import re
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime

R = pathlib.Path('/home/u566597497/.anthares-tiktok-restream')
ENABLED, LEASE = R / 'enabled', R / 'cloud-primary-lease'
SUP, LOG = R / 'supervisor.sh', R / 'supervisor.log'
TTL = 210

def emit(key, value):
    print('{}={}'.format(key, value), flush=True)

def atomic(path, text):
    fd, temp = tempfile.mkstemp(prefix='.cloud-lease-', dir=str(R))
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as stream:
            stream.write(text + '\n')
        os.replace(temp, str(path))
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

def current_mode():
    return ENABLED.read_text().strip() if ENABLED.is_file() else 'false'

def current_lease():
    if not LEASE.is_file():
        return '', 0
    values = LEASE.read_text().split()
    if len(values) != 2 or not re.match(r'^[0-9]{8,20}$', values[0]) or not values[1].isdigit():
        raise RuntimeError('INVALID_CLOUD_LEASE')
    return values[0], int(values[1])

def alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False

def matches(pid, needle):
    try:
        return needle.encode() in pathlib.Path('/proc/{}/cmdline'.format(pid)).read_bytes()
    except OSError:
        return False

def record(label):
    with LOG.open('a') as file:
        file.write(datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ') + ' ' + label + '\n')

def tick():
    subprocess.run(['/usr/bin/timeout', '--signal=TERM', '--kill-after=3', '23',
                    '/bin/bash', str(SUP), 'tick'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=28)

def to_host(event):
    atomic(ENABLED, 'true')
    if LEASE.exists():
        LEASE.unlink()
    record(event)
    try:
        tick()
    except (OSError, subprocess.TimeoutExpired):
        emit('CLOUD_HOST_TICK_RETRY_BY_CRON', 1)
    emit('CLOUD_HOST_REARMED', 1)

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else 'status'
    owner = sys.argv[2] if len(sys.argv) > 2 else ''
    if action not in ('status', 'recover', 'claim', 'heartbeat', 'release'):
        raise RuntimeError('INVALID_ACTION')
    if action in ('claim', 'heartbeat', 'release') and not re.match(r'^[0-9]{8,20}$', owner):
        raise RuntimeError('INVALID_OWNER')
    with (R / 'cloud-handoff.lock').open('a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        previous, expires = current_lease()
        state = current_mode()
        now = int(time.time())
        if action == 'status':
            emit('CLOUD_MODE', state)
            emit('CLOUD_LEASE_PRESENT', int(bool(previous)))
            if previous:
                emit('CLOUD_LEASE_SECONDS', expires - now)
            return
        if action == 'recover':
            if state == 'cloud' and expires <= now:
                to_host('CLOUD_LEASE_EXPIRED_HOST_REARM')
            else:
                emit('CLOUD_RECOVERY_NEEDED', 0)
            return
        if action == 'heartbeat':
            if state != 'cloud' or previous != owner or expires <= now:
                raise RuntimeError('CLOUD_HEARTBEAT_OWNER_LOST')
            atomic(LEASE, '{} {}'.format(owner, now + TTL))
            emit('CLOUD_HEARTBEAT', 'PASS')
            return
        if action == 'release':
            if state == 'cloud' and previous == owner:
                to_host('CLOUD_HANDOFF_RELEASED')
                emit('CLOUD_RELEASE', 'PASS')
                return
            if state == 'false' and previous == owner:
                LEASE.unlink()
                emit('CLOUD_OPERATOR_DISARMED', 1)
                return
            raise RuntimeError('CLOUD_RELEASE_OWNER_MISMATCH')
        if state != 'true' or previous:
            raise RuntimeError('CLOUD_CLAIM_NOT_ARMED')
        check = subprocess.run(['/bin/bash', str(SUP), 'status'], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, universal_newlines=True, timeout=12)
        if check.returncode or 'TIKTOK_HOSTINGER_SUPERVISOR=RUNNING' not in check.stdout or 'TIKTOK_HOSTINGER_FFMPEG=RUNNING' not in check.stdout:
            raise RuntimeError('CLOUD_CLAIM_HOST_UNHEALTHY')
        parent = int((R / 'supervisor.pid').read_text().strip())
        child = int((R / 'ffmpeg.pid').read_text().strip())
        if not matches(parent, str(SUP)) or not matches(child, 'ffmpeg.progress'):
            raise RuntimeError('CLOUD_CLAIM_PROCESS_MISMATCH')
        ppid = subprocess.check_output(['ps', '-p', str(child), '-o', 'ppid='],
                                      universal_newlines=True).strip()
        if int(ppid) != parent:
            raise RuntimeError('CLOUD_CLAIM_PARENT_MISMATCH')
        atomic(LEASE, '{} {}'.format(owner, now + TTL))
        atomic(ENABLED, 'cloud')
        try:
            os.kill(parent, signal.SIGTERM)
            for _ in range(30):
                if not alive(parent) and not alive(child):
                    break
                time.sleep(0.5)
            if alive(parent) or alive(child):
                raise RuntimeError('CLOUD_CLAIM_ORIGINAL_STILL_ALIVE')
        except Exception:
            to_host('CLOUD_CLAIM_ROLLBACK')
            raise
        record('CLOUD_HANDOFF_CLAIMED')
        emit('CLOUD_CLAIM', 'PASS')

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        emit('CLOUD_HANDOFF_ERROR', str(exc)[:90].replace(' ', '_'))
        sys.exit(1)
