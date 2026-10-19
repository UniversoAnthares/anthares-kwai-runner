"""GitHub-hosted SSH client; never sends work through Anthares Remote."""
import ipaddress
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('hosted GitHub execution required')
    if os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted':
        raise RuntimeError('self-hosted execution is forbidden')
    if os.environ.get('GITHUB_REPOSITORY') != 'UniversoAnthares/anthares-kwai-runner':
        raise RuntimeError('unexpected repository')
    mode = os.environ.get('SSH_RECOVERY_MODE', 'probe')
    if mode not in ('probe', 'recover'):
        raise RuntimeError('invalid mode')
    if mode == 'recover' and os.environ.get('AUTO_RECOVERY_ENABLED') != 'true':
        raise RuntimeError('automatic recovery is not activated')
    host = '100.89.147.45'
    assert ipaddress.ip_address(host) in ipaddress.ip_network('100.64.0.0/10')
    private = os.environ.pop('ARA_SSH_PRIVATE_KEY', '')
    host_key = os.environ.get('ARA_SSH_HOST_PUBLIC_KEY', '').strip()
    if not private or not host_key.startswith('ssh-ed25519 '):
        raise RuntimeError('SSH credential or pinned host key is missing')
    request_id = os.environ['GITHUB_RUN_ID'] + '-' + os.environ.get('GITHUB_RUN_ATTEMPT', '1')
    with tempfile.TemporaryDirectory(prefix='anthares-ssh-') as tmp:
        key = Path(tmp, 'id_ed25519')
        key.write_text(private.rstrip() + '\n')
        key.chmod(0o600)
        private = None
        known = Path(tmp, 'known_hosts')
        known.write_text(host + ' ' + host_key + '\n')
        known.chmod(0o600)
        command = ['ssh', '-F', '/dev/null', '-i', str(key),
                   '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
                   '-o', 'StrictHostKeyChecking=yes', '-o', f'UserKnownHostsFile={known}',
                   '-o', 'ConnectTimeout=15', '-o', 'ConnectionAttempts=1',
                   '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
                   '-T', 'Lucas@' + host]

        def invoke(operation):
            result = subprocess.run(command + [operation + ' ' + request_id],
                                    capture_output=True, text=True, timeout=45)
            if result.returncode:
                raise RuntimeError(f'SSH request failed (exit {result.returncode}): ' + result.stderr[-800:])
            data = json.loads(result.stdout.strip())
            if (data.get('schema') != 'anthares.ssh-recovery.v1'
                    or data.get('hostname') != 'DESKTOP-FTDK0HP'
                    or data.get('request_id') != request_id
                    or data.get('administrator') is not True):
                raise RuntimeError('SSH endpoint identity or privileges did not validate')
            print(json.dumps(data, separators=(',', ':')), flush=True)
            return data

        result = invoke('probe')
        print('SSH_INDEPENDENT_PROVEN=1 transport=openssh-over-tailscale executor=github-hosted', flush=True)
        if mode == 'probe':
            if result['action_performed']:
                raise RuntimeError('read-only probe performed a recovery action')
            return
        if result['primary_count'] or result['reserve_count']:
            print('SSH_RECOVERY_NOOP=existing-executor', flush=True)
            return
        # Observe locally through SSH every 15 seconds. Any gap >35 seconds
        # resets the Windows grace timer; a queued runner cannot skip the grace.
        for _ in range(8):
            result = invoke('observe')
            if result['decision'] != 'grace-period':
                break
            time.sleep(15)
        result = invoke('recover')
        if result['action_performed']:
            # Starting the watchdog is not proof the agent actually recovered.
            for _ in range(6):
                time.sleep(10)
                result = invoke('probe')
                if result['primary_count'] == 1 and result['reserve_count'] == 0:
                    print('SSH_CANONICAL_RECOVERY_PROVEN=1', flush=True)
                    return
            raise RuntimeError('watchdog started but canonical agent recovery is unproven')
        print('SSH_RECOVERY_NOOP=' + result['decision'], flush=True)


if __name__ == '__main__':
    main()
