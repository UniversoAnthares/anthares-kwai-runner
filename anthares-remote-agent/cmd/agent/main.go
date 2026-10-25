package main

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"time"
)

type Config struct {
	ControlURL         string
	DeviceToken        string
	DeviceID           string
	AllowShell         bool
	AllowedRoots       []string
	MaxConcurrent      int
	ARAControlPublic   ed25519.PublicKey
}

type Job struct {
	ID             string            `json:"id"`
	Type           string            `json:"type"`
	Args           map[string]string `json:"args"`
	TimeoutSeconds int               `json:"timeout_seconds"`
}

type JobEnvelope struct {
	Job *Job `json:"job"`
}

// jobSignature é o metadado assinado pelo plano de controle para jobs remote_job.
// Campos assinados: job_id, type, command_id, args, cwd, timeout_seconds, scope,
// token_identity, issued_at. O agente verifica a assinatura ed25519 e ignora
// qualquer scope presente nos args que não esteja assinado.
type jobSignature struct {
	Payload     string `json:"payload"`
	Sig         string `json:"sig"`
	IssuedAt    int64  `json:"issued_at"`
	ExpiresAt   int64  `json:"expires_at"`
}

type signedJobPayload struct {
	JobID         string   `json:"job_id"`
	Type          string   `json:"type"`
	CommandID     string   `json:"command_id"`
	Args          []string `json:"args"`
	Cwd           *string  `json:"cwd"`
	TimeoutSeconds int     `json:"timeout_seconds"`
	Scope         string   `json:"scope"`
	TokenIdentity string   `json:"token_identity"`
	IssuedAt      int64    `json:"issued_at"`
}

const seenJobsDirEnv = "ANTHARES_SEEN_JOBS_DIR"

func seenJobsRoot() string {
	if v := os.Getenv(seenJobsDirEnv); v != "" {
		return v
	}
	base := os.Getenv("PROGRAMDATA")
	if base == "" {
		base = os.TempDir()
	}
	return filepath.Join(base, "AntharesRemoteAgent", "seen-jobs")
}

// isJobIDSeen returns true if the job_id was already accepted within the
// retention window (signature expiry + 24h margin). It is used for replay
// protection: the same job_id must never be executed twice.
func isJobIDSeen(jobID string) bool {
	root := seenJobsRoot()
	path := filepath.Join(root, jobID+".seen")
	if _, err := os.Stat(path); err != nil {
		return false
	}
	info, err := os.Stat(path)
	if err != nil {
		return false
	}
	// Retention: signature expiry (60s) + 24h margin
	if time.Since(info.ModTime()) > 24*time.Hour+60*time.Second {
		_ = os.Remove(path)
		return false
	}
	return true
}

// recordJobID creates a marker file for an accepted job_id so it cannot be
// replayed. It is best-effort: if the file cannot be created, the job still
// proceeds (the signature remains the primary authorization).
func recordJobID(jobID string) error {
	root := seenJobsRoot()
	if err := os.MkdirAll(root, 0700); err != nil {
		return err
	}
	path := filepath.Join(root, jobID+".seen")
	f, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return err
	}
	return f.Close()
}

// cleanupSeenJobs removes marker files older than the retention window.
func cleanupSeenJobs() {
	root := seenJobsRoot()
	entries, err := os.ReadDir(root)
	if err != nil {
		return
	}
	cutoff := time.Now().Add(-(24*time.Hour + 60*time.Second))
	for _, e := range entries {
		if !strings.HasSuffix(e.Name(), ".seen") {
			continue
		}
		info, err := e.Info()
		if err != nil {
			continue
		}
		if info.ModTime().Before(cutoff) {
			_ = os.Remove(filepath.Join(root, e.Name()))
		}
	}
}

type Result struct {
	ID        string `json:"id"`
	OK        bool   `json:"ok"`
	Output    string `json:"output,omitempty"`
	Error     string `json:"error,omitempty"`
	StartedAt string `json:"started_at"`
	EndedAt   string `json:"ended_at"`
}

var httpClient = &http.Client{
	Timeout: 35 * time.Second,
	// Control-plane requests carry a device bearer token. Never follow
	// redirects: they can move jobs or credentials to an untrusted endpoint.
	CheckRedirect: func(req *http.Request, via []*http.Request) error {
		return http.ErrUseLastResponse
	},
}

func main() {
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

	sem := executionSemaphore(cfg.MaxConcurrent)
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

func loadConfig() (Config, error) {
	c := Config{
		ControlURL:    strings.TrimRight(os.Getenv("ANTHARES_CONTROL_URL"), "/"),
		DeviceToken:   os.Getenv("ANTHARES_DEVICE_TOKEN"),
		DeviceID:      os.Getenv("ANTHARES_DEVICE_ID"),
		AllowShell:    os.Getenv("ANTHARES_ALLOW_SHELL") == "1",
		MaxConcurrent: 4,
	}
	if v := os.Getenv("ARA_CONTROL_PUBLIC_KEY_B64"); v != "" {
		raw, err := base64.StdEncoding.DecodeString(v)
		if err == nil && len(raw) == ed25519.PublicKeySize {
			c.ARAControlPublic = ed25519.PublicKey(raw)
		}
	}
	if v, err := strconv.Atoi(os.Getenv("ANTHARES_MAX_CONCURRENT")); err == nil && v >= 1 && v <= 8 {
		c.MaxConcurrent = v
	}
	if roots := os.Getenv("ANTHARES_ALLOWED_ROOTS"); roots != "" {
		for _, root := range strings.Split(roots, ";") {
			root = strings.TrimSpace(root)
			if root != "" {
				if abs, err := filepath.Abs(root); err == nil {
					c.AllowedRoots = append(c.AllowedRoots, filepath.Clean(abs))
				}
			}
		}
	}
	if c.DeviceID == "" {
		return c, errors.New("ANTHARES_DEVICE_ID is required")
	}
	if c.ControlURL == "" {
		if !issueQueueConfigured() {
			return c, errors.New("no control transport configured")
		}
		return c, nil
	}
	if c.DeviceToken == "" {
		return c, errors.New("ANTHARES_DEVICE_TOKEN is required when HTTP control is configured")
	}
	u, err := url.Parse(c.ControlURL)
	if err != nil || u.Scheme != "https" || u.Hostname() == "" || u.User != nil || u.RawQuery != "" || u.Fragment != "" || (u.Path != "" && u.Path != "/") {
		return c, errors.New("ANTHARES_CONTROL_URL must be an HTTPS origin without credentials, path, query or fragment")
	}
	return c, nil
}

func authReq(req *http.Request, cfg Config) {
	req.Header.Set("Authorization", "Bearer "+cfg.DeviceToken)
	req.Header.Set("X-Anthares-Device", cfg.DeviceID)
	req.Header.Set("User-Agent", "AntharesRemoteAgent/0.3.1")
}

func heartbeatLoop(cfg Config) {
	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()
	failures := 0
	for {
		if err := heartbeat(cfg); err != nil {
			failures++
			fmt.Fprintf(os.Stderr, "heartbeat error (%d/4): %v\n", failures, err)
			if failures >= 4 {
				if issueQueueConfigured() {
					// GitHub/GitLab issue queues are independent transports. Keep the
					// process alive when HTTP control is unavailable so queue-only
					// recovery remains continuously reachable.
					fmt.Fprintln(os.Stderr, "control heartbeat unavailable; issue queue transport remains active")
					failures = 4
				} else {
					fmt.Fprintln(os.Stderr, "control heartbeat unavailable; exiting for supervisor recovery")
					os.Exit(23)
				}
			}
		} else {
			failures = 0
		}
		<-ticker.C
	}
}

func resultReplayLoop(cfg Config) {
	ticker := time.NewTicker(15 * time.Second)
	defer ticker.Stop()
	for range ticker.C {
		if err := replayEncryptedResults(cfg); err != nil {
			fmt.Fprintln(os.Stderr, "pending result replay deferred:", err)
		}
	}
}

func heartbeat(cfg Config) error {
	body, _ := json.Marshal(map[string]any{"device_id": cfg.DeviceID, "hostname": hostname(), "os": runtime.GOOS, "arch": runtime.GOARCH, "version": "0.3.1", "time": time.Now().UTC().Format(time.RFC3339)})
	req, _ := http.NewRequest(http.MethodPost, cfg.ControlURL+"/v1/device/heartbeat", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	authReq(req, cfg)
	resp, err := httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode/100 != 2 {
		return fmt.Errorf("heartbeat status %d", resp.StatusCode)
	}
	return nil
}

func pollJob(cfg Config) (*Job, error) {
	req, _ := http.NewRequest(http.MethodGet, cfg.ControlURL+"/v1/device/jobs/next", nil)
	authReq(req, cfg)
	resp, err := httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusNoContent {
		return nil, nil
	}
	if resp.StatusCode/100 != 2 {
		return nil, fmt.Errorf("poll status %d", resp.StatusCode)
	}
	// Read one extra byte so an oversized payload cannot be silently
	// accepted when its valid JSON prefix fits within the limit.
	payload, err := io.ReadAll(io.LimitReader(resp.Body, (1<<20)+1))
	if err != nil {
		return nil, err
	}
	if len(payload) > 1<<20 {
		return nil, errors.New("control plane job response exceeds 1 MiB")
	}
	var env JobEnvelope
	if err := json.Unmarshal(payload, &env); err != nil {
		return nil, err
	}
	if env.Job != nil {
		if err := validateJobID(env.Job.ID); err != nil {
			return nil, fmt.Errorf("control plane returned unsafe job ID: %w", err)
		}
		if strings.TrimSpace(env.Job.Type) == "" {
			return nil, errors.New("control plane returned job without type")
		}
	}
	return env.Job, nil
}

func executeJob(cfg Config, job Job) Result {
	start := time.Now().UTC()
	timeout := job.TimeoutSeconds
	if timeout <= 0 || timeout > 120 {
		timeout = 30
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(timeout)*time.Second)
	defer cancel()
	out, err := dispatch(ctx, cfg, job)
	r := Result{ID: job.ID, OK: err == nil, StartedAt: start.Format(time.RFC3339), EndedAt: time.Now().UTC().Format(time.RFC3339)}
	r.Output = out
	if err != nil {
		r.Error = err.Error()
	}
	return r
}

func boolArg(v string) bool {
	return v == "1" || strings.EqualFold(v, "true") || strings.EqualFold(v, "yes")
}

func dispatch(ctx context.Context, cfg Config, job Job) (string, error) {
	// Interactive desktop, clipboard, and active-window capture require a
	// separate, owner-approved per-action grant. None is issued by remote shell.
	if interactiveSurfaceRequiresOwnerConsent(job.Type) {
		return "", errors.New("owner authorization required for existing desktop, clipboard or window")
	}
	switch job.Type {
	case "ping":
		return "pong", nil
	case "agent_health":
		return agentHealthJSON(cfg)
	case "system_info":
		return systemInfoJSON(ctx)
	case "safe_environment":
		return safeEnvironmentJSON()
	case "network_info":
		return networkInfoJSON(ctx)
	case "tcp_connections":
		return tcpConnectionsJSON(ctx)
	case "scheduled_tasks":
		return scheduledTasksJSON(ctx)
	case "event_log":
		return eventLogJSON(ctx, job.Args["name"], job.Args["max"])
	case "process_list":
		return run(ctx, "tasklist", "/FO", "CSV")
	case "process_info":
		return processInfoJSON(ctx, job.Args["pid"])
	case "process_start":
		return processStartJSON(job.Args["path"], job.Args["args_json"])
	case "process_kill":
		return processKillJSON(job.Args["pid"])
	case "service_list":
		return serviceListJSON(ctx)
	case "service_status":
		return serviceStatusJSON(ctx, job.Args["name"])
	case "service_start":
		return serviceControlJSON(ctx, job.Args["name"], true)
	case "service_stop":
		return serviceControlJSON(ctx, job.Args["name"], false)
	case "clipboard_get":
		return run(ctx, "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", "Get-Clipboard -Raw")
	case "clipboard_set":
		return runWithStdin(ctx, job.Args["text"], "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", "$input | Set-Clipboard")
	case "screenshot":
		return screenshotBase64(ctx, job.Args["display"])
	case "file_acl":
		return fileACLJSON(ctx, cfg, job.Args["path"])
	case "file_stat":
		return fileStatJSON(cfg, job.Args["path"])
	case "file_list":
		return fileListJSON(cfg, job.Args["path"])
	case "file_mkdir":
		return fileMkdir(cfg, job.Args["path"])
	case "file_remove":
		return fileRemove(cfg, job.Args["path"], boolArg(job.Args["recursive"]))
	case "file_rename":
		return fileRename(cfg, job.Args["src"], job.Args["dst"])
	case "file_copy":
		return fileCopy(cfg, job.Args["src"], job.Args["dst"])
	case "file_sha256":
		return fileSHA256(cfg, job.Args["path"])
	case "file_write_atomic":
		b, err := base64.StdEncoding.DecodeString(job.Args["base64"])
		if err != nil {
			return "", err
		}
		return fileWriteAtomic(cfg, job.Args["path"], b)
	case "file_read_chunk":
		off, err := strconv.ParseInt(job.Args["offset"], 10, 64)
		if err != nil {
			return "", errors.New("invalid offset")
		}
		ln, err := strconv.ParseInt(job.Args["length"], 10, 64)
		if err != nil {
			return "", errors.New("invalid length")
		}
		return fileReadChunk(cfg, job.Args["path"], off, ln)
	case "file_write_chunk":
		off, err := strconv.ParseInt(job.Args["offset"], 10, 64)
		if err != nil {
			return "", errors.New("invalid offset")
		}
		return fileWriteChunk(cfg, job.Args["path"], off, job.Args["base64"], boolArg(job.Args["truncate"]))
	case "file_read":
		p, err := securePath(cfg, job.Args["path"])
		if err != nil {
			return "", err
		}
		b, err := os.ReadFile(p)
		if err != nil {
			return "", err
		}
		if len(b) > 1<<20 {
			return "", errors.New("file exceeds 1 MiB limit")
		}
		return base64.StdEncoding.EncodeToString(b), nil
	case "file_write":
		p, err := securePath(cfg, job.Args["path"])
		if err != nil {
			return "", err
		}
		b, err := base64.StdEncoding.DecodeString(job.Args["base64"])
		if err != nil {
			return "", err
		}
		if len(b) > 1<<20 {
			return "", errors.New("file exceeds 1 MiB limit")
		}
		return fileWriteAtomic(cfg, p, b)
	case "job_start":
		if !cfg.AllowShell {
			return "", errors.New("shell disabled")
		}
		if err := rejectInteractiveCommand(job.Args["command"]); err != nil {
			return "", err
		}
		return startDetachedJob(job.Args["command"], job.Args["name"])
	case "job_list":
		limit, _ := strconv.Atoi(job.Args["limit"])
		return jobListJSON(boolArg(job.Args["include_command"]), limit)
	case "job_status":
		return jobStatusJSON(job.Args["job_id"], boolArg(job.Args["include_command"]))
	case "job_logs":
		off := int64(-1)
		if v := job.Args["offset_bytes"]; v != "" {
			off, _ = strconv.ParseInt(v, 10, 64)
		}
		max, _ := strconv.Atoi(job.Args["max_bytes"])
		tail, _ := strconv.Atoi(job.Args["tail_lines"])
		return jobLogsJSON(job.Args["job_id"], off, max, tail)
	case "job_cancel":
		return jobCancelJSON(job.Args["job_id"])
	case "remote_job":
		return remoteJobJSON(ctx, cfg, job)
	case "shell":
		if !cfg.AllowShell {
			return "", errors.New("shell disabled; set ANTHARES_ALLOW_SHELL=1 to enable")
		}
		cmd := strings.TrimSpace(job.Args["command"])
		if cmd == "" {
			return "", errors.New("missing command")
		}
		// Structured, destination-allowlisted browser launch happens in the
		// active Windows user session, never through a SYSTEM shell.
		if handled, result, err := maybeHandleDesktopCommand(cmd); handled {
			return result, err
		}
		if err := rejectInteractiveCommand(cmd); err != nil {
			return "", err
		}
		shell := strings.ToLower(strings.TrimSpace(job.Args["shell"]))
		return shellExecJSON(ctx, shell, cmd)
	default:
		return "", fmt.Errorf("unsupported job type %q", job.Type)
	}
}

func safePath(cfg Config, p string) (string, error) { return securePath(cfg, p) }

func run(ctx context.Context, name string, args ...string) (string, error) {
	cmd := hiddenCommandContext(ctx, name, args...)
	var out bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &out
	err := cmd.Run()
	s := out.String()
	if len(s) > 1<<20 {
		s = s[:1<<20] + "\n[truncated]"
	}
	if ctx.Err() == context.DeadlineExceeded {
		return s, errors.New("command timed out")
	}
	return s, err
}

func runWithStdin(ctx context.Context, stdin, name string, args ...string) (string, error) {
	cmd := hiddenCommandContext(ctx, name, args...)
	cmd.Stdin = strings.NewReader(stdin)
	var out bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &out
	err := cmd.Run()
	if ctx.Err() == context.DeadlineExceeded {
		return out.String(), errors.New("command timed out")
	}
	return out.String(), err
}

func verifyJobSignature(cfg Config, job Job, sig jobSignature) (signedJobPayload, error) {
	var payload signedJobPayload
	if err := json.Unmarshal([]byte(sig.Payload), &payload); err != nil {
		return payload, errors.New("invalid job signature payload")
	}
	if payload.JobID != job.ID {
		return payload, errors.New("job signature job_id mismatch")
	}
	if payload.Type != job.Type {
		return payload, errors.New("job signature type mismatch")
	}
	now := time.Now().Unix()
	if sig.IssuedAt > 0 && now-sig.IssuedAt > 60 {
		return payload, errors.New("job signature issued too long ago")
	}
	if sig.ExpiresAt > 0 && time.Now().Unix() > sig.ExpiresAt {
		return payload, errors.New("job signature expired")
	}
	if cfg.ARAControlPublic == nil {
		return payload, errors.New("signing public key not configured")
	}
	sigBytes, err := base64.StdEncoding.DecodeString(sig.Sig)
	if err != nil || len(sigBytes) != ed25519.SignatureSize {
		return payload, errors.New("invalid job signature encoding")
	}
	signedBytes := append([]byte("ara-remote-job-v1\n"), []byte(sig.Payload)...)
	if !ed25519.Verify(cfg.ARAControlPublic, signedBytes, sigBytes) {
		return payload, errors.New("job signature verification failed")
	}
	if payload.Scope != "ara.exec" {
		return payload, errors.New("job signature scope is not ara.exec")
	}
	return payload, nil
}

// parseHandlerOutput interpreta o JSON devolvido pelo handler PowerShell.
// ok=false é tratado como FALHA do job, mesmo com exit code 0.
func parseHandlerOutput(out string) (bool, error) {
	var result struct {
		OK       bool   `json:"ok"`
		Error    string `json:"error,omitempty"`
		ExitCode int    `json:"exit_code,omitempty"`
	}
	if err := json.Unmarshal([]byte(out), &result); err != nil {
		return false, nil
	}
	if !result.OK {
		if result.Error == "" {
			result.Error = "handler_reported_failure"
		}
		return false, errors.New(result.Error)
	}
	return true, nil
}

func remoteJobJSON(ctx context.Context, cfg Config, job Job) (string, error) {
	sigRaw := job.Args["job_signature"]
	if sigRaw == "" {
		return "", errors.New("remote_job requires signed job metadata")
	}
	var sig jobSignature
	if err := json.Unmarshal([]byte(sigRaw), &sig); err != nil {
		return "", errors.New("invalid job_signature encoding")
	}
	signed, err := verifyJobSignature(cfg, job, sig)
	if err != nil {
		return "", err
	}
	if isJobIDSeen(signed.JobID) {
		return "", errors.New("job_id already executed: replay rejected")
	}
	if err := recordJobID(signed.JobID); err != nil {
		fmt.Fprintf(os.Stderr, "warning: could not record job_id %s for replay protection: %v\n", signed.JobID, err)
	}
	commandID := signed.CommandID
	if commandID == "" {
		return "", errors.New("missing command_id in signed job metadata")
	}
	argsJSON, _ := json.Marshal(signed.Args)
	cwd := ""
	if signed.Cwd != nil {
		cwd = *signed.Cwd
	}
	timeoutStr := strconv.Itoa(signed.TimeoutSeconds)

	payload := map[string]interface{}{
		"command_id":     commandID,
		"args":           string(argsJSON),
		"cwd":            cwd,
		"timeout_seconds": timeoutStr,
	}
	payloadBytes, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}

	bootstrapPath := `C:\ProgramData\Anthares\remote-job\remote-job-bootstrap.ps1`
	out, err := runWithStdin(ctx, string(payloadBytes), "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", bootstrapPath)
	if err != nil {
		return out, err
	}
	ok, perr := parseHandlerOutput(out)
	if !ok {
		return out, perr
	}
	return out, nil
}
func postResult(cfg Config, result Result) error {
	if err := validateJobID(result.ID); err != nil {
		return err
	}
	body, _ := json.Marshal(result)
	req, err := http.NewRequest(http.MethodPost, cfg.ControlURL+"/v1/device/jobs/"+url.PathEscape(result.ID)+"/result", bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	authReq(req, cfg)
	resp, err := httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode/100 != 2 {
		return fmt.Errorf("result status %d", resp.StatusCode)
	}
	return nil
}

func postResultRetry(cfg Config, result Result) error {
	if err := validateJobID(result.ID); err != nil {
		return err
	}
	var last error
	for attempt := 0; attempt < 5; attempt++ {
		if err := postResult(cfg, result); err == nil {
			return nil
		} else {
			last = err
		}
		if attempt < 4 {
			time.Sleep(time.Duration(1<<attempt) * time.Second)
		}
	}
	return last
}

func hostname() string { h, _ := os.Hostname(); return h }

// validateJobID prevents job IDs from escaping the control-plane result route.
func validateJobID(id string) error {
	if len(id) == 0 || len(id) > 128 {
		return errors.New("invalid job ID length")
	}
	for _, ch := range id {
		if !(ch >= 'a' && ch <= 'z' || ch >= 'A' && ch <= 'Z' || ch >= '0' && ch <= '9' || ch == '-' || ch == '_') {
			return errors.New("invalid job ID character")
		}
	}
	return nil
}
