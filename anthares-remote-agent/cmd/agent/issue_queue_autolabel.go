package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

// GitHub clients that bypass the canonical submitter can accidentally create a
// valid ARA job without ara-queued. This reconciler repairs only jobs that are:
//   - in the configured private queue repository,
//   - authored by the configured queue author,
//   - valid strict ARA envelopes for this device, and
//   - not already represented by a durable local receipt.
//
// The durable receipt check prevents completed jobs from being re-queued after
// the normal acknowledgement removes ara-queued.
func init() {
	if strings.TrimSpace(os.Getenv("ANTHARES_GITHUB_QUEUE_REPOSITORY")) == "" || strings.TrimSpace(os.Getenv("ANTHARES_GITHUB_QUEUE_TOKEN")) == "" {
		return
	}
	go githubAutoQueueLoop()
}

func githubAutoQueueLoop() {
	repo := strings.TrimSpace(os.Getenv("ANTHARES_GITHUB_QUEUE_REPOSITORY"))
	token := strings.TrimSpace(os.Getenv("ANTHARES_GITHUB_QUEUE_TOKEN"))
	author := strings.TrimSpace(os.Getenv("ANTHARES_GITHUB_QUEUE_AUTHOR"))
	if author == "" && strings.Count(repo, "/") == 1 {
		author = strings.SplitN(repo, "/", 2)[0]
	}
	provider := &githubIssueProvider{repo: repo, token: token, expectedAuthor: author}

	interval := 60 * time.Second
	if v, err := strconv.Atoi(strings.TrimSpace(os.Getenv("ANTHARES_GITHUB_AUTOQUEUE_INTERVAL_SECONDS"))); err == nil && v >= 30 && v <= 300 {
		interval = time.Duration(v) * time.Second
	}

	for {
		cfg, err := loadConfig()
		if err == nil {
			if n, err := provider.autoQueueMissingLabels(cfg.DeviceID); err != nil {
				fmt.Fprintf(os.Stderr, "github auto-queue reconciliation deferred: %v\n", err)
			} else if n > 0 {
				fmt.Fprintf(os.Stdout, "github auto-queue repaired=%d\n", n)
			}
		}
		time.Sleep(interval)
	}
}

func (p *githubIssueProvider) autoQueueMissingLabels(deviceID string) (int, error) {
	if err := p.verify(); err != nil {
		return 0, err
	}

	u := "https://api.github.com/repos/" + p.repo + "/issues?state=open&sort=created&direction=desc&per_page=100"
	req, _ := http.NewRequest(http.MethodGet, u, nil)
	p.auth(req)
	resp, err := httpClient.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode/100 != 2 {
		return 0, fmt.Errorf("GitHub auto-queue poll status %d", resp.StatusCode)
	}

	var issues []struct {
		Number      int    `json:"number"`
		Body        string `json:"body"`
		PullRequest any    `json:"pull_request"`
		User        struct{ Login string `json:"login"` } `json:"user"`
		Labels      []struct{ Name string `json:"name"` } `json:"labels"`
	}
	if err := json.NewDecoder(io.LimitReader(resp.Body, 8<<20)).Decode(&issues); err != nil {
		return 0, err
	}

	stateRoot, err := issueQueueStateDir()
	if err != nil {
		return 0, err
	}

	repaired := 0
	for _, issue := range issues {
		if issue.PullRequest != nil || issue.Number <= 0 {
			continue
		}
		if p.expectedAuthor != "" && !strings.EqualFold(issue.User.Login, p.expectedAuthor) {
			continue
		}
		queued := false
		for _, label := range issue.Labels {
			if strings.EqualFold(label.Name, "ara-queued") {
				queued = true
				break
			}
		}
		if queued {
			continue
		}

		job, err := decodeIssueQueueJob(issue.Body, deviceID)
		if err != nil {
			continue
		}
		if _, err := os.Stat(filepath.Join(stateRoot, job.ID+".json")); err == nil {
			continue
		} else if !os.IsNotExist(err) {
			continue
		}

		body, _ := json.Marshal(map[string][]string{"labels": {"ara-queued"}})
		labelReq, _ := http.NewRequest(
			http.MethodPost,
			"https://api.github.com/repos/"+p.repo+"/issues/"+strconv.Itoa(issue.Number)+"/labels",
			bytes.NewReader(body),
		)
		labelReq.Header.Set("Content-Type", "application/json")
		p.auth(labelReq)
		labelResp, err := httpClient.Do(labelReq)
		if err != nil {
			continue
		}
		io.Copy(io.Discard, io.LimitReader(labelResp.Body, 4096))
		labelResp.Body.Close()
		if labelResp.StatusCode/100 == 2 {
			repaired++
		}
	}
	return repaired, nil
}
