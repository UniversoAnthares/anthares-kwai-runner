package main

import (
	"bytes"
	"context"
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

const agentVersion = "0.4.0"

var defaultControlURLs = []string{
	"https://anthares-ara-vercel-reserve.vercel.app",
	"https://anthares-ara-controller-b.vercel.app",
	"https://anthares-ara-controller-c.vercel.app",
}

type Config struct {
	ControlURLs   []string
	DeviceToken   string
	DeviceID      string
	AllowShell    bool
	AllowedRoots  []string
	MaxConcurrent int
}

type ControllerLease struct {
	Origin string
	Epoch  string
}

type Job struct {
	ID             string            `json:"id"`
	Type           string            `json:"type"`
	Args           map[string]string `json:"args"`
	TimeoutSeconds int               `json:"timeout_seconds"`
	FenceEpoch     string            `json:"-"`
	Controller     string            `json:"-"`
}

type JobEnvelope struct {
	Job        *Job   `json:"job"`
	FenceEpoch string `json:"fence_epoch"`
}

type Result struct {
	ID         string `json:"id"`
	OK         bool   `json:"ok"`
	Output     string `json:"output,omitempty"`
	Error      string `json:"error,omitempty"`
	StartedAt  string `json:"started_at"`
	EndedAt    string `json:"ended_at"`
	FenceEpoch string `json:"fence_epoch"`
	Controller string `json:"controller"`
}

var httpClient = &http.Client{
	Timeout: 35 * time.Second,
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
	fmt.Printf("Anthares Remote Agent starting device=%s os=%s/%s concurrency=%d controllers=%d version=%s\n", cfg.DeviceID, runtime.GOOS, runtime.GOARCH, cfg.MaxConcurrent, len(cfg.ControlURLs), agentVersion)
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
		if err := validateJobID(job.ID); err != nil || strings.TrimSpace(job.Type) == "" || job.FenceEpoch == "" || job.Controller == "" {
			<-sem
			fmt.Fprintln(os.Stderr, "rejecting malformed or unfenced remote job")
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
		DeviceToken:   os.Getenv("ANTHARES_DEVICE_TOKEN"),
		DeviceID:      os.Getenv("ANTHARES_DEVICE_ID"),
		AllowShell:    os.Getenv("ANTHARES_ALLOW_SHELL") == "1",
		MaxConcurrent: 4,
	}
	rawURLs := strings.TrimSpace(os.Getenv("ANTHARES_CONTROL_URLS"))
	if rawURLs == "" {
		c.ControlURLs = append([]string(nil), defaultControlURLs...)
	} else {
		rawURLs = strings.ReplaceAll(rawURLs, ";", ",")
		for _, item := range strings.Split(rawURLs, ",") {
			if item = strings.TrimSpace(strings.TrimRight(item, "/")); item != "" {
				c.ControlURLs = append(c.ControlURLs, item)
			}
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
	if c.DeviceToken == "" || c.DeviceID == "" {
		return c, errors.New("ANTHARES_DEVICE_TOKEN and ANTHARES_DEVICE_ID are required")
	}
	if len(c.ControlURLs) != 3 {
		return c, errors.New("exactly three control origins are required")
	}
	seen := map[string]bool{}
	for i, origin := range c.ControlURLs {
		u, err := url.Parse(origin)
		if err != nil || u.Scheme != "https" || u.Hostname() == "" || u.User != nil || u.RawQuery != "" || u.Fragment != "" || (u.Path != "" && u.Path != "/") {
			return c, fmt.Errorf("control origin %d must be an HTTPS origin without credentials, path, query or fragment", i+1)
		}
		origin = strings.TrimRight(u.String(), "/")
		if seen[origin] {
			return c, errors.New("control origins must be distinct")
		}
		seen[origin] = true
		c.ControlURLs[i] = origin
	}
	return c, nil
}

func authReq(req *http.Request, cfg Config) {
	req.Header.Set("Authorization", "Bearer "+cfg.DeviceToken)
	req.Header.Set("X-Anthares-Device", cfg.DeviceID)
	req.Header.Set("User-Agent", "AntharesRemoteAgent/"+agentVersion)
}

func authReqEpoch(req *http.Request, cfg Config, epoch string) {
	authReq(req, cfg)
	if epoch != "" {
		req.Header.Set("X-Anthares-Fence-Epoch", epoch)
	}
}

func decodeLeaseResponse(resp *http.Response) (ControllerLease, bool) {
	if resp.StatusCode/100 != 2 {
		return ControllerLease{}, false
	}
	var v struct {
		Authenticated bool   `json:"authenticated"`
		FenceOwned   bool   `json:"fence_owned"`
		Acquired     bool   `json:"acquired"`
		Epoch        string `json:"epoch"`
	}
	if err := json.NewDecoder(io.LimitReader(resp.Body, 64<<10)).Decode(&v); err != nil {
		return ControllerLease{}, false
	}
	if v.Epoch == "" || (!v.FenceOwned && !v.Acquired) {
		return ControllerLease{}, false
	}
	if _, err := strconv.ParseUint(v.Epoch, 10, 64); err != nil {
		return ControllerLease{}, false
	}
	return ControllerLease{Epoch: v.Epoch}, true
}

func checkController(cfg Config, origin string) (ControllerLease, bool) {
	req, _ := http.NewRequest(http.MethodGet, origin+"/v1/device/auth-check", nil)
	authReq(req, cfg)
	resp, err := httpClient.Do(req)
	if err != nil {
		return ControllerLease{}, false
	}
	defer resp.Body.Close()
	lease, ok := decodeLeaseResponse(resp)
	if ok {
		lease.Origin = origin
	}
	return lease, ok
}

func acquireController(cfg Config, origin string) (ControllerLease, bool) {
	req, _ := http.NewRequest(http.MethodPost, origin+"/v1/device/fence/acquire", nil)
	authReq(req, cfg)
	resp, err := httpClient.Do(req)
	if err != nil {
		return ControllerLease{}, false
	}
	defer resp.Body.Close()
	lease, ok := decodeLeaseResponse(resp)
	if ok {
		lease.Origin = origin
	}
	return lease, ok
}

func chooseController(cfg Config, allowAcquire bool) (ControllerLease, error) {
	for _, origin := range cfg.ControlURLs {
		if lease, ok := checkController(cfg, origin); ok {
			return lease, nil
		}
	}
	if allowAcquire {
		for _, origin := range cfg.ControlURLs {
			if lease, ok := acquireController(cfg, origin); ok {
				return lease, nil
			}
		}
	}
	return ControllerLease{}, errors.New("no fenced controller available")
}

func heartbeatLoop(cfg Config) {
	ticker := time.NewTicker(15 * time.Second)
	defer ticker.Stop()
	for {
		_ = heartbeat(cfg)
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
	lease, err := chooseController(cfg, true)
	if err != nil {
		return err
	}
	body, _ := json.Marshal(map[string]any{"device_id": cfg.DeviceID, "hostname": hostname(), "os": runtime.GOOS, "arch": runtime.GOARCH, "version": agentVersion, "time": time.Now().UTC().Format(time.RFC3339)})
	req, _ := http.NewRequest(http.MethodPost, lease.Origin+"/v1/device/heartbeat", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	authReqEpoch(req, cfg, lease.Epoch)
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
	lease, err := chooseController(cfg, true)
	if err != nil {
		return nil, err
	}
	req, _ := http.NewRequest(http.MethodGet, lease.Origin+"/v1/device/jobs/next", nil)
	authReqEpoch(req, cfg, lease.Epoch)
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
		if env.FenceEpoch == "" || env.FenceEpoch != lease.Epoch {
			return nil, errors.New("control plane returned mismatched fence epoch")
		}
		env.Job.FenceEpoch = env.FenceEpoch
		env.Job.Controller = lease.Origin
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
	r := Result{ID: job.ID, OK: err == nil, StartedAt: start.Format(time.RFC3339), EndedAt: time.Now().UTC().Format(time.RFC3339), FenceEpoch: job.FenceEpoch, Controller: job.Controller}
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
	switch job.Type {
	case "ping":
		return "pong", nil
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
	case "shell":
		if !cfg.AllowShell {
			return "", errors.New("shell disabled; set ANTHARES_ALLOW_SHELL=1 to enable")
		}
		cmd := strings.TrimSpace(job.Args["command"])
		if cmd == "" {
			return "", errors.New("missing command")
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

func resultFenceStillValid(cfg Config, result Result) bool {
	if result.Controller == "" || result.FenceEpoch == "" {
		return false
	}
	lease, ok := checkController(cfg, result.Controller)
	return ok && lease.Epoch == result.FenceEpoch
}

func postResult(cfg Config, result Result) error {
	if err := validateJobID(result.ID); err != nil {
		return err
	}
	if !resultFenceStillValid(cfg, result) {
		return errors.New("stale fence epoch; result quarantined")
	}
	body, _ := json.Marshal(result)
	req, err := http.NewRequest(http.MethodPost, result.Controller+"/v1/device/jobs/"+url.PathEscape(result.ID)+"/result", bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	authReqEpoch(req, cfg, result.FenceEpoch)
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
			if strings.Contains(err.Error(), "stale fence epoch") || strings.Contains(err.Error(), "result status 423") || strings.Contains(err.Error(), "result status 409") || strings.Contains(err.Error(), "result status 404") {
				return err
			}
		}
		if attempt < 4 {
			time.Sleep(time.Duration(1<<attempt) * time.Second)
		}
	}
	return last
}

func hostname() string { h, _ := os.Hostname(); return h }

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
