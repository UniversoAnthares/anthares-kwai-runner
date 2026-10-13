#!/usr/bin/env python3
from pathlib import Path
import re

main = Path('anthares-remote-agent/cmd/agent/main.go')
s = main.read_text(encoding='utf-8')

old_main = re.compile(r'''func main\(\) \{.*?\n\}\n\nfunc loadConfig\(\) \(Config, error\) \{''', re.S)
new_main = r'''func main() {
	cfg, err := loadConfig()
	if err != nil {
		fmt.Fprintln(os.Stderr, "config error:", err)
		os.Exit(2)
	}
	fmt.Printf("Anthares Remote Agent starting device=%s os=%s/%s concurrency=%d\n", cfg.DeviceID, runtime.GOOS, runtime.GOARCH, cfg.MaxConcurrent)

	// GitHub/GitLab issue queues are a complete, independent control transport.
	// When no HTTP origin is configured, run cleanly in queue-only mode instead
	// of manufacturing a fake endpoint and producing permanent network failures.
	if strings.TrimSpace(cfg.ControlURL) == "" {
		if !issueQueueConfigured() {
			fmt.Fprintln(os.Stderr, "config error: no control transport configured")
			os.Exit(2)
		}
		fmt.Println("Anthares Remote Agent running in issue-queue-only mode")
		select {}
	}

	go heartbeatLoop(cfg)
	if err := replayEncryptedResults(cfg); err != nil {
		fmt.Fprintln(os.Stderr, "pending result replay deferred:", err)
	}
	go resultReplayLoop(cfg)

	sem := make(chan struct{}, cfg.MaxConcurrent)
	for {
		sem <- struct{}{}
		job, err := pollJob(cfg)
		if err != nil {
			<-sem
			fmt.Fprintln(os.Stderr, "poll error:", err)
			time.Sleep(3 * time.Second)
			continue
		}
		if job == nil {
			<-sem
			time.Sleep(2 * time.Second)
			continue
		}
		if err := validateJobID(job.ID); err != nil || strings.TrimSpace(job.Type) == "" {
			<-sem
			fmt.Fprintln(os.Stderr, "rejecting malformed remote job")
			continue
		}
		j := *job
		go func() {
			defer func() { <-sem }()
			result := executeJob(cfg, j)
			if err := saveEncryptedResult(resultSpoolDir(cfg), cfg.DeviceToken, result); err != nil {
				fmt.Fprintf(os.Stderr, "fatal result spool error job=%s: %v\n", result.ID, err)
				os.Exit(1)
			}
			if err := postResultRetry(cfg, result); err != nil {
				fmt.Fprintf(os.Stderr, "result upload deferred job=%s: %v\n", result.ID, err)
				return
			}
			if err := os.Remove(filepath.Join(resultSpoolDir(cfg), result.ID+".pending")); err != nil {
				fmt.Fprintf(os.Stderr, "result cleanup deferred job=%s: %v\n", result.ID, err)
			}
		}()
	}
}

func loadConfig() (Config, error) {'''
s, n = old_main.subn(lambda _m: new_main, s, count=1)
if n != 1:
    raise SystemExit('main/loadConfig patch target missing')

old_validation = '''\tif c.ControlURL == "" || c.DeviceToken == "" || c.DeviceID == "" {
\t\treturn c, errors.New("ANTHARES_CONTROL_URL, ANTHARES_DEVICE_TOKEN and ANTHARES_DEVICE_ID are required")
\t}
\tu, err := url.Parse(c.ControlURL)
\tif err != nil || u.Scheme != "https" || u.Hostname() == "" || u.User != nil || u.RawQuery != "" || u.Fragment != "" || (u.Path != "" && u.Path != "/") {
\t\treturn c, errors.New("ANTHARES_CONTROL_URL must be an HTTPS origin without credentials, path, query or fragment")
\t}
'''
new_validation = '''\tif c.DeviceID == "" {
\t\treturn c, errors.New("ANTHARES_DEVICE_ID is required")
\t}
\tif c.ControlURL == "" {
\t\tif !issueQueueConfigured() {
\t\t\treturn c, errors.New("no control transport configured")
\t\t}
\t\treturn c, nil
\t}
\tif c.DeviceToken == "" {
\t\treturn c, errors.New("ANTHARES_DEVICE_TOKEN is required when HTTP control is configured")
\t}
\tu, err := url.Parse(c.ControlURL)
\tif err != nil || u.Scheme != "https" || u.Hostname() == "" || u.User != nil || u.RawQuery != "" || u.Fragment != "" || (u.Path != "" && u.Path != "/") {
\t\treturn c, errors.New("ANTHARES_CONTROL_URL must be an HTTPS origin without credentials, path, query or fragment")
\t}
'''
if old_validation not in s:
    raise SystemExit('loadConfig validation target missing')
s = s.replace(old_validation, new_validation, 1)
main.write_text(s, encoding='utf-8')

issue = Path('anthares-remote-agent/cmd/agent/issue_queue.go')
s = issue.read_text(encoding='utf-8')
old_init = re.compile(r'''func init\(\) \{.*?\n\}\n\nfunc issueQueueConfigured''', re.S)
new_init = r'''func init() {
	if !issueQueueConfigured() {
		return
	}
	go func() {
		cfg, err := loadConfig()
		if err != nil {
			fmt.Fprintln(os.Stderr, "issue queue config error:", err)
			return
		}
		issueQueueLoop(cfg)
	}()
}

func issueQueueConfigured'''
s, n = old_init.subn(lambda _m: new_init, s, count=1)
if n != 1:
    raise SystemExit('issue queue init target missing')

old_state = '''\tif runtime.GOOS == "windows" {
\t\treturn `C:\\ProgramData\\AntharesRemoteAgent\\issue-queue`, nil
\t}
'''
new_state = '''\tif runtime.GOOS == "windows" {
\t\tif work := strings.TrimSpace(os.Getenv("ANTHARES_WORK_ROOT")); work != "" {
\t\t\treturn filepath.Join(work, "ara-jobs", "issue-queue"), nil
\t\t}
\t\treturn `C:\\ProgramData\\AntharesRemoteAgent\\issue-queue`, nil
\t}
'''
if old_state in s:
    s = s.replace(old_state, new_state, 1)
elif 'filepath.Join(work, "ara-jobs", "issue-queue")' not in s:
    raise SystemExit('issue queue state-dir target missing')
issue.write_text(s, encoding='utf-8')

sup = Path('anthares-remote-agent/windows/run-agent-system-supervisor.ps1')
s = sup.read_text(encoding='utf-8')
legacy_preferred = "$exe = if (Test-Path $legacyExe) { $legacyExe } elseif (Test-Path $v4Exe) { $v4Exe } else { $legacyExe }"
v4_preferred = "$exe = if (Test-Path $v4Exe) { $v4Exe } elseif (Test-Path $legacyExe) { $legacyExe } else { $v4Exe }"
if legacy_preferred in s:
    s = s.replace(legacy_preferred, v4_preferred, 1)
elif v4_preferred not in s:
    raise SystemExit('supervisor binary preference target missing')
s = s.replace('# The installed production binary already proved an end-to-end private queue ping.', '# The queue-aware v4 binary is canonical after a proven private GitHub queue round trip.')
if 'onrender.com' in s or 'workers.dev' in s:
    raise SystemExit('forbidden Render/Cloudflare runtime origin remains in supervisor')
if "Remove-Item Env:ANTHARES_CONTROL_URL" not in s or "mode='issue-queues-only'" not in s:
    raise SystemExit('supervisor is not queue-only')
if 'cloudflare_required=$false' not in s or 'render_required=$false' not in s:
    raise SystemExit('supervisor dependency flags are not fail-closed')
sup.write_text(s, encoding='utf-8')

print('ARA_QUEUE_ONLY_FINALIZED=1')
