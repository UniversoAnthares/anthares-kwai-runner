#!/usr/bin/env python3
from pathlib import Path

main = Path('anthares-remote-agent/cmd/agent/main.go')
s = main.read_text(encoding='utf-8')

# Keep this finalizer idempotent. Current main.go may already contain the
# queue-only transport validation; only tighten HTTP idle/error polling.
s = s.replace('time.Sleep(10 * time.Second)\n\t\t\tcontinue', 'time.Sleep(3 * time.Second)\n\t\t\tcontinue', 1)
s = s.replace('time.Sleep(15 * time.Second)\n\t\t\tcontinue', 'time.Sleep(2 * time.Second)\n\t\t\tcontinue', 1)
required_main = [
    'Anthares Remote Agent running in issue-queue-only mode',
    'if c.ControlURL == "" {',
    'if !issueQueueConfigured() {',
    'ANTHARES_DEVICE_TOKEN is required when HTTP control is configured',
]
missing = [x for x in required_main if x not in s]
if missing:
    raise SystemExit('main queue-only invariant missing: ' + ', '.join(missing))
main.write_text(s, encoding='utf-8')

issue = Path('anthares-remote-agent/cmd/agent/issue_queue.go')
s = issue.read_text(encoding='utf-8')
required_issue = [
    'go func() {',
    'issueQueueLoop(cfg)',
    'filepath.Join(work, "ara-jobs", "issue-queue")',
    'workers := cfg.MaxConcurrent',
    'seen := make(map[string]bool)',
]
missing = [x for x in required_issue if x not in s]
if missing:
    raise SystemExit('issue queue invariant missing: ' + ', '.join(missing))
issue.write_text(s, encoding='utf-8')

# Supervisor files are maintained directly and validated by CI. Keeping this
# finalizer scoped to Go avoids clobbering concurrent supervisor hardening.
print('ARA_QUEUE_ONLY_FINALIZED=1')
