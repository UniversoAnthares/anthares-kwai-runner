package main

import (
	"bytes"
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
	"sync"
	"time"
)

const issueQueueResultChunk = 45000

type issueQueueEnvelope struct {
	JobID          string            `json:"job_id"`
	DeviceID       string            `json:"device_id"`
	Type           string            `json:"type"`
	Args           map[string]string `json:"args,omitempty"`
	TimeoutSeconds int               `json:"timeout_seconds,omitempty"`
}

type issueQueueReceipt struct {
	JobID     string  `json:"job_id"`
	State     string  `json:"state"`
	Provider  string  `json:"provider,omitempty"`
	Source    string  `json:"source,omitempty"`
	StartedAt string  `json:"started_at,omitempty"`
	UpdatedAt string  `json:"updated_at"`
	Result    *Result `json:"result,omitempty"`
}

type issueQueueItem struct {
	Provider issueQueueProvider
	Source   string
	Job      Job
}

type issueQueueProvider interface {
	Name() string
	Poll(deviceID string) ([]issueQueueItem, error)
	Acknowledge(item issueQueueItem, result Result) error
}

type githubIssueProvider struct {
	repo           string
	token          string
	expectedAuthor string
	verifyOnce     sync.Once
	verifyErr      error
}

type gitlabIssueProvider struct {
	project        string
	token          string
	expectedAuthor string
	verifyOnce     sync.Once
	verifyErr      error
}

func init() {
	// Issue queues are a control-plane-independent transport. If no HTTP control
	// origin is configured, keep the existing agent main loop alive on a reserved
	// non-routable origin while the issue queue goroutine performs real work.
	if !issueQueueConfigured() {
		return
	}
	if strings.TrimSpace(os.Getenv("ANTHARES_CONTROL_URL")) == "" {
		_ = os.Setenv("ANTHARES_CONTROL_URL", "https://ara-control-unavailable.invalid")
	}
	if strings.TrimSpace(os.Getenv("ANTHARES_DEVICE_TOKEN")) == "" {
		_ = os.Setenv("ANTHARES_DEVICE_TOKEN", "issue-queue-only")
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

func issueQueueConfigured() bool {
	gh := strings.TrimSpace(os.Getenv("ANTHARES_GITHUB_QUEUE_REPOSITORY")) != "" && strings.TrimSpace(os.Getenv("ANTHARES_GITHUB_QUEUE_TOKEN")) != ""
	gl := strings.TrimSpace(os.Getenv("ANTHARES_GITLAB_QUEUE_PROJECT")) != "" && strings.TrimSpace(os.Getenv("ANTHARES_GITLAB_QUEUE_TOKEN")) != ""
	return gh || gl
}

func issueQueueProviders() []issueQueueProvider {
	var out []issueQueueProvider
	if repo, token := strings.TrimSpace(os.Getenv("ANTHARES_GITHUB_QUEUE_REPOSITORY")), strings.TrimSpace(os.Getenv("ANTHARES_GITHUB_QUEUE_TOKEN")); repo != "" && token != "" {
		author := strings.TrimSpace(os.Getenv("ANTHARES_GITHUB_QUEUE_AUTHOR"))
		if author == "" {
			author = strings.SplitN(repo, "/", 2)[0]
		}
		out = append(out, &githubIssueProvider{repo: repo, token: token, expectedAuthor: author})
	}
	if project, token := strings.TrimSpace(os.Getenv("ANTHARES_GITLAB_QUEUE_PROJECT")), strings.TrimSpace(os.Getenv("ANTHARES_GITLAB_QUEUE_TOKEN")); project != "" && token != "" {
		out = append(out, &gitlabIssueProvider{project: project, token: token, expectedAuthor: strings.TrimSpace(os.Getenv("ANTHARES_GITLAB_QUEUE_AUTHOR"))})
	}
	return out
}

func issueQueueLoop(cfg Config) {
	providers := issueQueueProviders()
	if len(providers) == 0 {
		return
	}
	interval := 20 * time.Second
	if v, err := strconv.Atoi(strings.TrimSpace(os.Getenv("ANTHARES_ISSUE_QUEUE_INTERVAL_SECONDS"))); err == nil && v >= 10 && v <= 300 {
		interval = time.Duration(v) * time.Second
	}
	fmt.Fprintf(os.Stdout, "Anthares issue queue enabled providers=%d interval=%s\n", len(providers), interval)
	for {
		for _, provider := range providers {
			items, err := provider.Poll(cfg.DeviceID)
			if err != nil {
				fmt.Fprintf(os.Stderr, "issue queue poll deferred provider=%s: %v\n", provider.Name(), err)
				continue
			}
			for _, item := range items {
				if err := processIssueQueueItem(cfg, item); err != nil {
					fmt.Fprintf(os.Stderr, "issue queue item deferred provider=%s source=%s: %v\n", provider.Name(), item.Source, err)
				}
			}
		}
		time.Sleep(interval)
	}
}

func processIssueQueueItem(cfg Config, item issueQueueItem) error {
	if item.Job.ID == "" {
		return errors.New("missing job ID")
	}
	if err := validateJobID(item.Job.ID); err != nil {
		return err
	}
	root, err := issueQueueStateDir()
	if err != nil {
		return err
	}
	if err := os.MkdirAll(root, 0700); err != nil {
		return err
	}
	path := filepath.Join(root, item.Job.ID+".json")
	started := time.Now().UTC()
	receipt := issueQueueReceipt{JobID: item.Job.ID, State: "started", Provider: item.Provider.Name(), Source: item.Source, StartedAt: started.Format(time.RFC3339), UpdatedAt: started.Format(time.RFC3339)}
	created, existing, err := createOrReadIssueQueueReceipt(path, receipt)
	if err != nil {
		return err
	}
	if !created {
		if existing.Result != nil {
			return item.Provider.Acknowledge(item, *existing.Result)
		}
		uncertain := Result{ID: item.Job.ID, OK: false, Error: "uncertain prior execution state; automatic replay refused", StartedAt: existing.StartedAt, EndedAt: time.Now().UTC().Format(time.RFC3339)}
		existing.State = "uncertain"
		existing.UpdatedAt = time.Now().UTC().Format(time.RFC3339)
		existing.Result = &uncertain
		if err := writeIssueQueueReceipt(path, existing); err != nil {
			return err
		}
		return item.Provider.Acknowledge(item, uncertain)
	}

	result := executeJob(cfg, item.Job)
	if result.OK {
		receipt.State = "done"
	} else {
		receipt.State = "failed"
	}
	receipt.Result = &result
	receipt.UpdatedAt = time.Now().UTC().Format(time.RFC3339)
	if err := writeIssueQueueReceipt(path, receipt); err != nil {
		return err
	}
	return item.Provider.Acknowledge(item, result)
}

func issueQueueStateDir() (string, error) {
	if v := strings.TrimSpace(os.Getenv("ANTHARES_ISSUE_QUEUE_STATE_DIR")); v != "" {
		return filepath.Abs(v)
	}
	if runtime.GOOS == "windows" {
		return `C:\ProgramData\AntharesRemoteAgent\issue-queue`, nil
	}
	base, err := os.UserCacheDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(base, "anthares-remote-agent", "issue-queue"), nil
}

func createOrReadIssueQueueReceipt(path string, receipt issueQueueReceipt) (bool, issueQueueReceipt, error) {
	b, err := json.Marshal(receipt)
	if err != nil {
		return false, issueQueueReceipt{}, err
	}
	f, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err == nil {
		if _, werr := f.Write(b); werr != nil {
			_ = f.Close()
			return false, issueQueueReceipt{}, werr
		}
		if serr := f.Sync(); serr != nil {
			_ = f.Close()
			return false, issueQueueReceipt{}, serr
		}
		if cerr := f.Close(); cerr != nil {
			return false, issueQueueReceipt{}, cerr
		}
		return true, receipt, nil
	}
	if !os.IsExist(err) {
		return false, issueQueueReceipt{}, err
	}
	b, err = os.ReadFile(path)
	if err != nil {
		return false, issueQueueReceipt{}, err
	}
	var existing issueQueueReceipt
	if err := json.Unmarshal(b, &existing); err != nil {
		return false, issueQueueReceipt{}, fmt.Errorf("invalid existing issue queue receipt: %w", err)
	}
	return false, existing, nil
}

func writeIssueQueueReceipt(path string, receipt issueQueueReceipt) error {
	b, err := json.Marshal(receipt)
	if err != nil {
		return err
	}
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, b, 0600); err != nil {
		return err
	}
	return os.Rename(tmp, path)
}

func decodeIssueQueueJob(body, deviceID string) (Job, error) {
	if len(body) == 0 || len(body) > 1<<20 {
		return Job{}, errors.New("invalid issue queue body size")
	}
	var env issueQueueEnvelope
	dec := json.NewDecoder(strings.NewReader(body))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&env); err != nil {
		return Job{}, err
	}
	if env.DeviceID != deviceID {
		return Job{}, errors.New("job targets another device")
	}
	if err := validateJobID(env.JobID); err != nil {
		return Job{}, err
	}
	if strings.TrimSpace(env.Type) == "" {
		return Job{}, errors.New("missing job type")
	}
	if env.TimeoutSeconds < 0 || env.TimeoutSeconds > 120 {
		return Job{}, errors.New("invalid timeout")
	}
	return Job{ID: env.JobID, Type: strings.TrimSpace(env.Type), Args: env.Args, TimeoutSeconds: env.TimeoutSeconds}, nil
}

func (p *githubIssueProvider) Name() string { return "github" }

func (p *githubIssueProvider) verify() error {
	p.verifyOnce.Do(func() {
		if strings.Count(p.repo, "/") != 1 {
			p.verifyErr = errors.New("invalid GitHub queue repository")
			return
		}
		req, _ := http.NewRequest(http.MethodGet, "https://api.github.com/repos/"+p.repo, nil)
		p.auth(req)
		resp, err := httpClient.Do(req)
		if err != nil {
			p.verifyErr = err
			return
		}
		defer resp.Body.Close()
		if resp.StatusCode/100 != 2 {
			p.verifyErr = fmt.Errorf("GitHub repository verification status %d", resp.StatusCode)
			return
		}
		var meta struct{ Private bool `json:"private"` }
		if err := json.NewDecoder(io.LimitReader(resp.Body, 1<<20)).Decode(&meta); err != nil {
			p.verifyErr = err
			return
		}
		if !meta.Private {
			p.verifyErr = errors.New("refusing public GitHub queue repository")
		}
	})
	return p.verifyErr
}

func (p *githubIssueProvider) auth(req *http.Request) {
	req.Header.Set("Authorization", "Bearer "+p.token)
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("X-GitHub-Api-Version", "2022-11-28")
	req.Header.Set("User-Agent", "AntharesRemoteAgent/0.4.0")
}

func (p *githubIssueProvider) Poll(deviceID string) ([]issueQueueItem, error) {
	if err := p.verify(); err != nil {
		return nil, err
	}
	u := "https://api.github.com/repos/" + p.repo + "/issues?state=open&labels=ara-queued&per_page=30"
	req, _ := http.NewRequest(http.MethodGet, u, nil)
	p.auth(req)
	resp, err := httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode/100 != 2 {
		return nil, fmt.Errorf("GitHub issue poll status %d", resp.StatusCode)
	}
	var issues []struct {
		Number      int    `json:"number"`
		Body        string `json:"body"`
		PullRequest any    `json:"pull_request"`
		User        struct{ Login string `json:"login"` } `json:"user"`
	}
	if err := json.NewDecoder(io.LimitReader(resp.Body, 4<<20)).Decode(&issues); err != nil {
		return nil, err
	}
	var out []issueQueueItem
	for _, issue := range issues {
		if issue.PullRequest != nil || issue.Number <= 0 {
			continue
		}
		if p.expectedAuthor != "" && !strings.EqualFold(issue.User.Login, p.expectedAuthor) {
			continue
		}
		job, err := decodeIssueQueueJob(issue.Body, deviceID)
		if err != nil {
			continue
		}
		out = append(out, issueQueueItem{Provider: p, Source: strconv.Itoa(issue.Number), Job: job})
	}
	return out, nil
}

func (p *githubIssueProvider) Acknowledge(item issueQueueItem, result Result) error {
	n, err := strconv.Atoi(item.Source)
	if err != nil || n <= 0 {
		return errors.New("invalid GitHub issue source")
	}
	payload, _ := json.Marshal(result)
	if err := p.postResultChunks("https://api.github.com/repos/"+p.repo+"/issues/"+strconv.Itoa(n)+"/comments", payload); err != nil {
		return err
	}
	req, _ := http.NewRequest(http.MethodDelete, "https://api.github.com/repos/"+p.repo+"/issues/"+strconv.Itoa(n)+"/labels/ara-queued", nil)
	p.auth(req)
	resp, err := httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusNotFound && resp.StatusCode/100 != 2 {
		return fmt.Errorf("GitHub acknowledgement status %d", resp.StatusCode)
	}
	return nil
}

func (p *githubIssueProvider) postResultChunks(endpoint string, payload []byte) error {
	encoded := base64.StdEncoding.EncodeToString(payload)
	parts := splitASCII(encoded, issueQueueResultChunk)
	for i, part := range parts {
		message := fmt.Sprintf("ARA_RESULT_B64 part=%d/%d\n%s", i+1, len(parts), part)
		body, _ := json.Marshal(map[string]string{"body": message})
		req, _ := http.NewRequest(http.MethodPost, endpoint, bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		p.auth(req)
		resp, err := httpClient.Do(req)
		if err != nil {
			return err
		}
		io.Copy(io.Discard, io.LimitReader(resp.Body, 4096))
		resp.Body.Close()
		if resp.StatusCode/100 != 2 {
			return fmt.Errorf("GitHub result comment status %d", resp.StatusCode)
		}
	}
	return nil
}

func (p *gitlabIssueProvider) Name() string { return "gitlab" }

func (p *gitlabIssueProvider) apiProject() string { return url.PathEscape(p.project) }

func (p *gitlabIssueProvider) auth(req *http.Request) {
	req.Header.Set("PRIVATE-TOKEN", p.token)
	req.Header.Set("User-Agent", "AntharesRemoteAgent/0.4.0")
}

func (p *gitlabIssueProvider) verify() error {
	p.verifyOnce.Do(func() {
		if strings.Count(p.project, "/") < 1 {
			p.verifyErr = errors.New("invalid GitLab queue project")
			return
		}
		req, _ := http.NewRequest(http.MethodGet, "https://gitlab.com/api/v4/projects/"+p.apiProject(), nil)
		p.auth(req)
		resp, err := httpClient.Do(req)
		if err != nil {
			p.verifyErr = err
			return
		}
		defer resp.Body.Close()
		if resp.StatusCode/100 != 2 {
			p.verifyErr = fmt.Errorf("GitLab project verification status %d", resp.StatusCode)
			return
		}
		var meta struct{ Visibility string `json:"visibility"` }
		if err := json.NewDecoder(io.LimitReader(resp.Body, 1<<20)).Decode(&meta); err != nil {
			p.verifyErr = err
			return
		}
		if strings.EqualFold(meta.Visibility, "public") {
			p.verifyErr = errors.New("refusing public GitLab queue project")
		}
	})
	return p.verifyErr
}

func (p *gitlabIssueProvider) Poll(deviceID string) ([]issueQueueItem, error) {
	if err := p.verify(); err != nil {
		return nil, err
	}
	u := "https://gitlab.com/api/v4/projects/" + p.apiProject() + "/issues?state=opened&labels=ara-queued&per_page=30"
	req, _ := http.NewRequest(http.MethodGet, u, nil)
	p.auth(req)
	resp, err := httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode/100 != 2 {
		return nil, fmt.Errorf("GitLab issue poll status %d", resp.StatusCode)
	}
	var issues []struct {
		IID         int    `json:"iid"`
		Description string `json:"description"`
		Author      struct{ Username string `json:"username"` } `json:"author"`
	}
	if err := json.NewDecoder(io.LimitReader(resp.Body, 4<<20)).Decode(&issues); err != nil {
		return nil, err
	}
	var out []issueQueueItem
	for _, issue := range issues {
		if issue.IID <= 0 {
			continue
		}
		if p.expectedAuthor != "" && !strings.EqualFold(issue.Author.Username, p.expectedAuthor) {
			continue
		}
		job, err := decodeIssueQueueJob(issue.Description, deviceID)
		if err != nil {
			continue
		}
		out = append(out, issueQueueItem{Provider: p, Source: strconv.Itoa(issue.IID), Job: job})
	}
	return out, nil
}

func (p *gitlabIssueProvider) Acknowledge(item issueQueueItem, result Result) error {
	iid, err := strconv.Atoi(item.Source)
	if err != nil || iid <= 0 {
		return errors.New("invalid GitLab issue source")
	}
	payload, _ := json.Marshal(result)
	encoded := base64.StdEncoding.EncodeToString(payload)
	parts := splitASCII(encoded, issueQueueResultChunk)
	base := "https://gitlab.com/api/v4/projects/" + p.apiProject() + "/issues/" + strconv.Itoa(iid)
	for i, part := range parts {
		message := fmt.Sprintf("ARA_RESULT_B64 part=%d/%d\n%s", i+1, len(parts), part)
		body, _ := json.Marshal(map[string]string{"body": message})
		req, _ := http.NewRequest(http.MethodPost, base+"/notes", bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		p.auth(req)
		resp, err := httpClient.Do(req)
		if err != nil {
			return err
		}
		io.Copy(io.Discard, io.LimitReader(resp.Body, 4096))
		resp.Body.Close()
		if resp.StatusCode/100 != 2 {
			return fmt.Errorf("GitLab result note status %d", resp.StatusCode)
		}
	}
	body, _ := json.Marshal(map[string]string{"remove_labels": "ara-queued", "add_labels": "ara-done"})
	req, _ := http.NewRequest(http.MethodPut, base, bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	p.auth(req)
	resp, err := httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode/100 != 2 {
		return fmt.Errorf("GitLab acknowledgement status %d", resp.StatusCode)
	}
	return nil
}

func splitASCII(s string, n int) []string {
	if n <= 0 || len(s) <= n {
		return []string{s}
	}
	parts := make([]string, 0, (len(s)+n-1)/n)
	for len(s) > n {
		parts = append(parts, s[:n])
		s = s[n:]
	}
	if s != "" {
		parts = append(parts, s)
	}
	return parts
}
