#!/usr/bin/env python3
from pathlib import Path


def replace_block(source: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    return source[:start] + replacement.rstrip() + "\n\n" + source[end:]


main = Path('anthares-remote-agent/cmd/agent/main.go')
s = main.read_text(encoding='utf-8')

# Keep this finalizer idempotent. Current main.go may already contain the
# queue-only transport validation; only tighten HTTP idle/error polling.
s = s.replace('time.Sleep(10 * time.Second)\n\t\t\tcontinue', 'time.Sleep(3 * time.Second)\n\t\t\tcontinue', 1)
s = s.replace('time.Sleep(15 * time.Second)\n\t\t\tcontinue', 'time.Sleep(2 * time.Second)\n\t\t\tcontinue', 1)
s = s.replace('sem := make(chan struct{}, cfg.MaxConcurrent)', 'sem := executionSemaphore(cfg.MaxConcurrent)', 1)
required_main = [
    'Anthares Remote Agent running in issue-queue-only mode',
    'if c.ControlURL == "" {',
    'if !issueQueueConfigured() {',
    'ANTHARES_DEVICE_TOKEN is required when HTTP control is configured',
    'sem := executionSemaphore(cfg.MaxConcurrent)',
]
missing = [x for x in required_main if x not in s]
if missing:
    raise SystemExit('main queue-only invariant missing: ' + ', '.join(missing))
main.write_text(s, encoding='utf-8')

issue = Path('anthares-remote-agent/cmd/agent/issue_queue.go')
s = issue.read_text(encoding='utf-8')

# Provider loops are independent: a slow GitHub or GitLab poll cannot hold up
# the other provider. Jobs are dispatched through one persistent bounded pool,
# and an in-flight map prevents the same job_id from executing concurrently
# when both providers expose it. The worker semaphore is process-global so HTTP
# and both issue queues together never exceed ANTHARES_MAX_CONCURRENT.
queue_loop = r'''func issueQueueLoop(cfg Config) {
	providers := issueQueueProviders()
	if len(providers) == 0 {
		return
	}
	interval := 20 * time.Second
	if v, err := strconv.Atoi(strings.TrimSpace(os.Getenv("ANTHARES_ISSUE_QUEUE_INTERVAL_SECONDS"))); err == nil && v >= 10 && v <= 300 {
		interval = time.Duration(v) * time.Second
	}
	fmt.Fprintf(os.Stdout, "Anthares issue queue enabled providers=%d interval=%s\n", len(providers), interval)

	workers := cfg.MaxConcurrent
	if workers < 1 {
		workers = 1
	}
	sem := executionSemaphore(workers)
	items := make(chan issueQueueItem, workers*len(providers)*4)
	inFlight := make(map[string]bool)
	var inFlightMu sync.Mutex

	for _, provider := range providers {
		go func(provider issueQueueProvider) {
			for {
				polled, err := provider.Poll(cfg.DeviceID)
				if err != nil {
					fmt.Fprintf(os.Stderr, "issue queue poll deferred provider=%s: %v\n", provider.Name(), err)
				} else {
					for _, item := range polled {
						items <- item
					}
				}
				time.Sleep(interval)
			}
		}(provider)
	}

	for item := range items {
		if item.Job.ID == "" {
			continue
		}
		inFlightMu.Lock()
		if inFlight[item.Job.ID] {
			inFlightMu.Unlock()
			continue
		}
		select {
		case sem <- struct{}{}:
			inFlight[item.Job.ID] = true
			inFlightMu.Unlock()
			go func(item issueQueueItem) {
				defer func() {
					<-sem
					inFlightMu.Lock()
					delete(inFlight, item.Job.ID)
					inFlightMu.Unlock()
				}()
				if err := processIssueQueueItem(cfg, item); err != nil {
					fmt.Fprintf(os.Stderr, "issue queue item deferred provider=%s source=%s: %v\n", item.Provider.Name(), item.Source, err)
				}
			}(item)
		default:
			// Leave the job queued. The provider will rediscover it on the next
			// poll rather than blocking discovery behind long-running work.
			inFlightMu.Unlock()
		}
	}
}'''
s = replace_block(s, 'func issueQueueLoop(cfg Config) {', 'func processIssueQueueItem(cfg Config, item issueQueueItem) error {', queue_loop)

# Poll every page (100 issues/page, capped defensively) so backlog beyond the
# first API page cannot starve indefinitely.
github_poll = r'''func (p *githubIssueProvider) Poll(deviceID string) ([]issueQueueItem, error) {
	if err := p.verify(); err != nil {
		return nil, err
	}
	var out []issueQueueItem
	for page := 1; page <= 20; page++ {
		u := "https://api.github.com/repos/" + p.repo + "/issues?state=open&labels=ara-queued&per_page=100&page=" + strconv.Itoa(page)
		req, _ := http.NewRequest(http.MethodGet, u, nil)
		p.auth(req)
		resp, err := httpClient.Do(req)
		if err != nil {
			return nil, err
		}
		if resp.StatusCode/100 != 2 {
			resp.Body.Close()
			return nil, fmt.Errorf("GitHub issue poll status %d", resp.StatusCode)
		}
		var issues []struct {
			Number      int    `json:"number"`
			Body        string `json:"body"`
			PullRequest any    `json:"pull_request"`
			User        struct{ Login string `json:"login"` } `json:"user"`
		}
		err = json.NewDecoder(io.LimitReader(resp.Body, 8<<20)).Decode(&issues)
		resp.Body.Close()
		if err != nil {
			return nil, err
		}
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
		if len(issues) < 100 {
			break
		}
	}
	return out, nil
}'''
s = replace_block(s, 'func (p *githubIssueProvider) Poll(deviceID string) ([]issueQueueItem, error) {', 'func (p *githubIssueProvider) Acknowledge(item issueQueueItem, result Result) error {', github_poll)

gitlab_poll = r'''func (p *gitlabIssueProvider) Poll(deviceID string) ([]issueQueueItem, error) {
	if err := p.verify(); err != nil {
		return nil, err
	}
	var out []issueQueueItem
	for page := 1; page <= 20; page++ {
		u := "https://gitlab.com/api/v4/projects/" + p.apiProject() + "/issues?state=opened&labels=ara-queued&per_page=100&page=" + strconv.Itoa(page)
		req, _ := http.NewRequest(http.MethodGet, u, nil)
		p.auth(req)
		resp, err := httpClient.Do(req)
		if err != nil {
			return nil, err
		}
		if resp.StatusCode/100 != 2 {
			resp.Body.Close()
			return nil, fmt.Errorf("GitLab issue poll status %d", resp.StatusCode)
		}
		var issues []struct {
			IID         int    `json:"iid"`
			Description string `json:"description"`
			Author      struct{ Username string `json:"username"` } `json:"author"`
		}
		err = json.NewDecoder(io.LimitReader(resp.Body, 8<<20)).Decode(&issues)
		resp.Body.Close()
		if err != nil {
			return nil, err
		}
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
		if len(issues) < 100 {
			break
		}
	}
	return out, nil
}'''
s = replace_block(s, 'func (p *gitlabIssueProvider) Poll(deviceID string) ([]issueQueueItem, error) {', 'func (p *gitlabIssueProvider) Acknowledge(item issueQueueItem, result Result) error {', gitlab_poll)

required_issue = [
    'go func(provider issueQueueProvider)',
    'inFlight := make(map[string]bool)',
    'sem := executionSemaphore(workers)',
    'per_page=100&page=',
    'for page := 1; page <= 20; page++',
    'filepath.Join(work, "ara-jobs", "issue-queue")',
]
missing = [x for x in required_issue if x not in s]
if missing:
    raise SystemExit('issue queue invariant missing: ' + ', '.join(missing))
issue.write_text(s, encoding='utf-8')

limiter = Path('anthares-remote-agent/cmd/agent/execution_limiter.go')
limiter.write_text('''package main

import "sync"

var processExecutionLimiter struct {
    once sync.Once
    ch   chan struct{}
}

// executionSemaphore returns the single process-wide execution budget shared
// by HTTP, GitHub and GitLab transports. All callers use the same configured
// MaxConcurrent value from the same environment.
func executionSemaphore(max int) chan struct{} {
    if max < 1 {
        max = 1
    }
    processExecutionLimiter.once.Do(func() {
        processExecutionLimiter.ch = make(chan struct{}, max)
    })
    return processExecutionLimiter.ch
}
''', encoding='utf-8')

print('ARA_QUEUE_ONLY_FINALIZED=1')
