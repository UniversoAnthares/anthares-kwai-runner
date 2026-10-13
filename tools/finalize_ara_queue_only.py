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
s, n = old_main.subn(new_main, s, count=1)
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
s, n = old_init.subn(new_init, s, count=1)
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
if old_state not in s:
    raise SystemExit('issue queue state-dir target missing')
s = s.replace(old_state, new_state, 1)
issue.write_text(s, encoding='utf-8')

sup = Path('anthares-remote-agent/windows/run-agent-system-supervisor.ps1')
s = sup.read_text(encoding='utf-8')
s = s.replace("# Prefer the already-proven production binary; v4 remains a fallback until it\n# has passed an end-to-end Windows heartbeat/job validation.", "# The queue-aware v4 binary is canonical after a proven private GitHub queue\n# round trip. Legacy remains rollback-only.")
s = s.replace("$exe = if (Test-Path $legacyExe) { $legacyExe } elseif (Test-Path $v4Exe) { $v4Exe } else { $legacyExe }", "$exe = if (Test-Path $v4Exe) { $v4Exe } elseif (Test-Path $legacyExe) { $legacyExe } else { $v4Exe }")

# No default HTTP provider. Render and Cloudflare are explicitly excluded from
# automatic runtime selection; a future independent HTTPS origin must be set
# explicitly through ANTHARES_CONTROL_*.
start = s.index('function Control-OrDefault')
end = s.index('\n$created = $false', start)
control_block = r'''function Control-OrDefault([string]$value) {
    $candidate = ([string]$value).Trim().TrimEnd('/')
    if ([string]::IsNullOrWhiteSpace($candidate)) { return '' }
    if ($candidate -match 'onrender\.com' -or $candidate -match 'workers\.dev') { return '' }
    return $candidate
}
$primaryControl = Control-OrDefault $env:ANTHARES_CONTROL_PRIMARY_URL
$secondaryControl = Control-OrDefault $env:ANTHARES_CONTROL_SECONDARY_URL
$tertiaryControl = Control-OrDefault $env:ANTHARES_CONTROL_TERTIARY_URL
$httpCandidates = @($primaryControl, $secondaryControl, $tertiaryControl) |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
    Select-Object -Unique
'''
s = s[:start] + control_block + s[end:]
s = s.replace("'Global\\AntharesRemoteSystemSupervisorV6'", "'Global\\AntharesRemoteSystemSupervisorV7'")
s = s.replace('cloudflare_controls=$true; render_required=$false', 'cloudflare_controls=$false; cloudflare_required=$false; render_required=$false')
s = s.replace("if ($queueReady) { $mode = if ($active) { 'issue-queues+cloudflare-http' } else { 'issue-queues-only' } }", "if ($queueReady) { $mode = if ($active) { 'issue-queues+http' } else { 'issue-queues-only' } }")
s = s.replace("elseif ($active) { $mode = 'cloudflare-http-only' }", "elseif ($active) { $mode = 'http-only' }")
s = s.replace("$reason = if ($currentControlHealthy) { 'running-queue-with-cloudflare-http' } else { 'running-queue-failover' }", "$reason = if ($currentControlHealthy) { 'running-queue-with-http' } else { 'running-queue-only' }")

old_existing = """        $existing = @(Get-Process -Name 'anthares-remote-agent','anthares-remote-agent-standard','anthares-remote-agent-v4' -ErrorAction SilentlyContinue)
        if ($existing.Count -gt 0) { Save-State '' 'preserve-existing' 'waiting-for-existing-agent'; Start-Sleep -Seconds 5; continue }
"""
new_existing = """        $existing = @(Get-Process -Name 'anthares-remote-agent','anthares-remote-agent-standard','anthares-remote-agent-v4' -ErrorAction SilentlyContinue)
        if ($existing.Count -gt 0) {
            $desiredName = Split-Path $exe -Leaf
            $desiredRunning = @($existing | Where-Object { $_.ProcessName -eq [IO.Path]::GetFileNameWithoutExtension($desiredName) })
            if ($desiredRunning.Count -gt 0) { Save-State '' 'preserve-existing' 'desired-agent-already-running' $desiredRunning[0].Id; Start-Sleep -Seconds 5; continue }
            Save-State '' 'migrating' 'replacing-legacy-agent'
            foreach ($p in $existing) { try { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } catch {} }
            Start-Sleep -Seconds 2
            continue
        }
"""
if old_existing not in s:
    raise SystemExit('supervisor existing-process target missing')
s = s.replace(old_existing, new_existing, 1)
sup.write_text(s, encoding='utf-8')

print('ARA_QUEUE_ONLY_FINALIZED=1')
