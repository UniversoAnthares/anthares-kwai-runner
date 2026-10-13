package main

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"
)

const executionLedgerVersion = 1

var (
	executionLedgerMu sync.Mutex
	errExecutionBusy  = errors.New("execution already leased")
)

type executionMeta struct {
	Transport      string
	Source         string
	IdempotencyKey string
	CreatedAt      string
	ExpiresAt      string
}

type executionLedgerFile struct {
	Version      int                         `json:"version"`
	FenceCounter uint64                      `json:"fence_counter"`
	Jobs         map[string]*executionRecord `json:"jobs"`
}

type executionRecord struct {
	JobID          string            `json:"job_id"`
	IdempotencyKey string            `json:"idempotency_key"`
	Transport      string            `json:"transport"`
	Source         string            `json:"source,omitempty"`
	Type           string            `json:"type"`
	Args           map[string]string `json:"args,omitempty"`
	Status         string            `json:"status"`
	CreatedAt      string            `json:"created_at,omitempty"`
	LeasedAt       string            `json:"leased_at,omitempty"`
	StartedAt      string            `json:"started_at,omitempty"`
	CompletedAt    string            `json:"completed_at,omitempty"`
	AcknowledgedAt string            `json:"acknowledged_at,omitempty"`
	Result         *Result           `json:"result,omitempty"`
	ResultHash     string            `json:"result_hash,omitempty"`
	Attempt        int               `json:"attempt"`
	Owner          string            `json:"owner,omitempty"`
	LeaseToken     string            `json:"lease_token,omitempty"`
	FencingToken   uint64            `json:"fencing_token"`
	LeaseUntil     string            `json:"lease_until,omitempty"`
}

type executionAcquire struct {
	Action     string
	JobID      string
	LeaseToken string
	Record     executionRecord
}

func executionLedgerPath() (string, error) {
	if v := strings.TrimSpace(os.Getenv("ANTHARES_EXECUTION_LEDGER_PATH")); v != "" {
		return filepath.Abs(v)
	}
	root := strings.TrimSpace(os.Getenv("ANTHARES_WORK_ROOT"))
	if root == "" {
		if runtimeRoot := strings.TrimSpace(os.Getenv("ANTHARES_RUNTIME_ROOT")); runtimeRoot != "" {
			root = runtimeRoot
		}
	}
	if root == "" {
		if os.PathSeparator == '\\' {
			root = `D:\AntharesWork\AntharesRemote`
		} else {
			cache, err := os.UserCacheDir()
			if err != nil {
				return "", err
			}
			root = filepath.Join(cache, "anthares-remote-agent")
		}
	}
	return filepath.Join(root, "state", "execution-ledger.json"), nil
}

func emptyExecutionLedger() executionLedgerFile {
	return executionLedgerFile{Version: executionLedgerVersion, Jobs: map[string]*executionRecord{}}
}

func readExecutionLedger(path string) (executionLedgerFile, error) {
	b, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		return emptyExecutionLedger(), nil
	}
	if err != nil {
		return executionLedgerFile{}, err
	}
	var ledger executionLedgerFile
	if err := json.Unmarshal(b, &ledger); err != nil {
		return executionLedgerFile{}, err
	}
	if ledger.Version == 0 {
		ledger.Version = executionLedgerVersion
	}
	if ledger.Jobs == nil {
		ledger.Jobs = map[string]*executionRecord{}
	}
	return ledger, nil
}

func writeExecutionLedger(path string, ledger executionLedgerFile) error {
	if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		return err
	}
	b, err := json.MarshalIndent(ledger, "", "  ")
	if err != nil {
		return err
	}
	tmp := path + ".tmp." + strconv.Itoa(os.Getpid())
	if err := os.WriteFile(tmp, b, 0600); err != nil {
		return err
	}
	f, err := os.OpenFile(tmp, os.O_RDWR, 0600)
	if err == nil {
		_ = f.Sync()
		_ = f.Close()
	}
	if err := os.Rename(tmp, path); err != nil {
		_ = os.Remove(tmp)
		return err
	}
	return nil
}

func cloneArgs(in map[string]string) map[string]string {
	if len(in) == 0 {
		return nil
	}
	out := make(map[string]string, len(in))
	for k, v := range in {
		out[k] = v
	}
	return out
}

func newLeaseToken() (string, error) {
	b := make([]byte, 16)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return hex.EncodeToString(b), nil
}

func executionOwner() string {
	host, _ := os.Hostname()
	return fmt.Sprintf("%s:%d", host, os.Getpid())
}

func executionLeaseDuration(job Job) time.Duration {
	seconds := job.TimeoutSeconds
	if seconds <= 0 || seconds > 120 {
		seconds = 30
	}
	d := time.Duration(seconds+30) * time.Second
	if d < 120*time.Second {
		d = 120 * time.Second
	}
	return d
}

func executionReplaySafe(jobType string) bool {
	switch strings.TrimSpace(jobType) {
	case "ping", "system_info", "safe_environment", "network_info", "tcp_connections", "scheduled_tasks", "event_log", "process_list", "process_info", "service_list", "service_status", "file_acl", "file_stat", "file_list", "file_sha256", "file_read", "file_read_chunk", "job_status":
		return true
	default:
		return false
	}
}

func parseLedgerTime(v string) time.Time {
	if strings.TrimSpace(v) == "" {
		return time.Time{}
	}
	t, err := time.Parse(time.RFC3339Nano, v)
	if err != nil {
		return time.Time{}
	}
	return t.UTC()
}

func findExecutionRecord(ledger executionLedgerFile, jobID, idem string) *executionRecord {
	if rec := ledger.Jobs[jobID]; rec != nil {
		return rec
	}
	if idem == "" {
		return nil
	}
	for _, rec := range ledger.Jobs {
		if rec != nil && rec.IdempotencyKey == idem {
			return rec
		}
	}
	return nil
}

func validateExecutionMeta(job Job, meta executionMeta) error {
	if err := validateJobID(job.ID); err != nil {
		return err
	}
	if strings.TrimSpace(job.Type) == "" {
		return errors.New("missing job type")
	}
	if meta.IdempotencyKey == "" {
		meta.IdempotencyKey = job.ID
	}
	if len(meta.IdempotencyKey) > 160 {
		return errors.New("idempotency key too long")
	}
	if meta.CreatedAt != "" {
		created, err := time.Parse(time.RFC3339Nano, meta.CreatedAt)
		if err != nil {
			return errors.New("invalid created_at")
		}
		if created.After(time.Now().UTC().Add(5 * time.Minute)) {
			return errors.New("created_at is in the future")
		}
	}
	if meta.ExpiresAt != "" {
		expires, err := time.Parse(time.RFC3339Nano, meta.ExpiresAt)
		if err != nil {
			return errors.New("invalid expires_at")
		}
		if !expires.After(time.Now().UTC()) {
			return errors.New("job expired")
		}
	}
	return nil
}

func acquireExecution(job Job, meta executionMeta) (executionAcquire, error) {
	if meta.IdempotencyKey == "" {
		meta.IdempotencyKey = job.ID
	}
	if err := validateExecutionMeta(job, meta); err != nil {
		return executionAcquire{}, err
	}
	path, err := executionLedgerPath()
	if err != nil {
		return executionAcquire{}, err
	}
	executionLedgerMu.Lock()
	defer executionLedgerMu.Unlock()
	ledger, err := readExecutionLedger(path)
	if err != nil {
		return executionAcquire{}, err
	}
	now := time.Now().UTC()
	existing := findExecutionRecord(ledger, job.ID, meta.IdempotencyKey)
	if existing != nil {
		switch existing.Status {
		case "completed", "failed", "acknowledged":
			if existing.Result != nil {
				return executionAcquire{Action: "cached", JobID: existing.JobID, Record: *existing}, nil
			}
		case "leased", "running":
			if until := parseLedgerTime(existing.LeaseUntil); until.After(now) {
				return executionAcquire{Action: "busy", JobID: existing.JobID, Record: *existing}, errExecutionBusy
			}
			if !executionReplaySafe(existing.Type) {
				uncertain := Result{ID: existing.JobID, OK: false, Error: "uncertain prior execution state; automatic replay refused", StartedAt: existing.StartedAt, EndedAt: now.Format(time.RFC3339Nano)}
				existing.Status = "uncertain"
				existing.CompletedAt = now.Format(time.RFC3339Nano)
				existing.LeaseUntil = ""
				existing.LeaseToken = ""
				existing.Result = &uncertain
				existing.ResultHash = hashResult(uncertain)
				if err := writeExecutionLedger(path, ledger); err != nil {
					return executionAcquire{}, err
				}
				return executionAcquire{Action: "cached", JobID: existing.JobID, Record: *existing}, nil
			}
		case "uncertain":
			if !executionReplaySafe(existing.Type) && existing.Result != nil {
				return executionAcquire{Action: "cached", JobID: existing.JobID, Record: *existing}, nil
			}
		}
	}

	token, err := newLeaseToken()
	if err != nil {
		return executionAcquire{}, err
	}
	ledger.FenceCounter++
	attempt := 1
	createdAt := meta.CreatedAt
	if createdAt == "" {
		createdAt = now.Format(time.RFC3339Nano)
	}
	if existing != nil {
		attempt = existing.Attempt + 1
		if existing.CreatedAt != "" {
			createdAt = existing.CreatedAt
		}
	}
	rec := &executionRecord{
		JobID:          job.ID,
		IdempotencyKey: meta.IdempotencyKey,
		Transport:      meta.Transport,
		Source:         meta.Source,
		Type:           job.Type,
		Args:           cloneArgs(job.Args),
		Status:         "leased",
		CreatedAt:      createdAt,
		LeasedAt:       now.Format(time.RFC3339Nano),
		Attempt:        attempt,
		Owner:          executionOwner(),
		LeaseToken:     token,
		FencingToken:   ledger.FenceCounter,
		LeaseUntil:     now.Add(executionLeaseDuration(job)).Format(time.RFC3339Nano),
	}
	if existing != nil && existing.JobID != job.ID {
		delete(ledger.Jobs, existing.JobID)
	}
	ledger.Jobs[job.ID] = rec
	if err := writeExecutionLedger(path, ledger); err != nil {
		return executionAcquire{}, err
	}
	return executionAcquire{Action: "execute", JobID: job.ID, LeaseToken: token, Record: *rec}, nil
}

func markExecutionRunning(jobID, leaseToken string) error {
	path, err := executionLedgerPath()
	if err != nil {
		return err
	}
	executionLedgerMu.Lock()
	defer executionLedgerMu.Unlock()
	ledger, err := readExecutionLedger(path)
	if err != nil {
		return err
	}
	rec := ledger.Jobs[jobID]
	if rec == nil || rec.LeaseToken != leaseToken {
		return errors.New("fencing rejection at start")
	}
	rec.Status = "running"
	rec.StartedAt = time.Now().UTC().Format(time.RFC3339Nano)
	return writeExecutionLedger(path, ledger)
}

func hashResult(result Result) string {
	b, _ := json.Marshal(result)
	sum := sha256.Sum256(b)
	return hex.EncodeToString(sum[:])
}

func completeExecution(jobID, leaseToken string, result Result) error {
	path, err := executionLedgerPath()
	if err != nil {
		return err
	}
	executionLedgerMu.Lock()
	defer executionLedgerMu.Unlock()
	ledger, err := readExecutionLedger(path)
	if err != nil {
		return err
	}
	rec := ledger.Jobs[jobID]
	if rec == nil || rec.LeaseToken != leaseToken {
		return errors.New("fencing rejection at completion")
	}
	if result.OK {
		rec.Status = "completed"
	} else {
		rec.Status = "failed"
	}
	rec.CompletedAt = time.Now().UTC().Format(time.RFC3339Nano)
	rec.Result = &result
	rec.ResultHash = hashResult(result)
	rec.LeaseUntil = ""
	return writeExecutionLedger(path, ledger)
}

func acknowledgeExecution(jobID string) error {
	path, err := executionLedgerPath()
	if err != nil {
		return err
	}
	executionLedgerMu.Lock()
	defer executionLedgerMu.Unlock()
	ledger, err := readExecutionLedger(path)
	if err != nil {
		return err
	}
	rec := ledger.Jobs[jobID]
	if rec == nil {
		return nil
	}
	if rec.Status == "completed" || rec.Status == "failed" || rec.Status == "acknowledged" || rec.Status == "uncertain" {
		rec.Status = "acknowledged"
		rec.AcknowledgedAt = time.Now().UTC().Format(time.RFC3339Nano)
	}
	return writeExecutionLedger(path, ledger)
}

func executeJobTracked(cfg Config, job Job, meta executionMeta) (Result, bool, error) {
	acq, err := acquireExecution(job, meta)
	if err != nil {
		if errors.Is(err, errExecutionBusy) {
			return Result{}, false, err
		}
		return Result{}, false, err
	}
	if acq.Action == "cached" {
		if acq.Record.Result == nil {
			return Result{}, false, errors.New("cached execution has no result")
		}
		return *acq.Record.Result, false, nil
	}
	if acq.Action != "execute" {
		return Result{}, false, fmt.Errorf("unexpected execution action %q", acq.Action)
	}
	if err := markExecutionRunning(acq.JobID, acq.LeaseToken); err != nil {
		return Result{}, false, err
	}
	result := executeJob(cfg, job)
	if err := completeExecution(acq.JobID, acq.LeaseToken, result); err != nil {
		return Result{}, true, err
	}
	return result, true, nil
}
