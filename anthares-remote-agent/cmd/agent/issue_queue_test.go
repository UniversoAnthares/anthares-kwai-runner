package main

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

type fakeIssueProvider struct {
	acks    int
	results []Result
}

func (p *fakeIssueProvider) Name() string { return "fake" }
func (p *fakeIssueProvider) Poll(string) ([]issueQueueItem, error) { return nil, nil }
func (p *fakeIssueProvider) Acknowledge(_ issueQueueItem, result Result) error {
	p.acks++
	p.results = append(p.results, result)
	return nil
}

func TestDecodeIssueQueueJob(t *testing.T) {
	job, err := decodeIssueQueueJob(`{"job_id":"abc-123","device_id":"DESKTOP-FTDK0HP","type":"ping","timeout_seconds":15}`, "DESKTOP-FTDK0HP")
	if err != nil {
		t.Fatal(err)
	}
	if job.ID != "abc-123" || job.Type != "ping" || job.TimeoutSeconds != 15 {
		t.Fatalf("unexpected job: %#v", job)
	}
}

func TestDecodeIssueQueueJobRejectsUnknownAndWrongDevice(t *testing.T) {
	if _, err := decodeIssueQueueJob(`{"job_id":"abc","device_id":"other","type":"ping"}`, "DESKTOP-FTDK0HP"); err == nil {
		t.Fatal("expected wrong-device rejection")
	}
	if _, err := decodeIssueQueueJob(`{"job_id":"abc","device_id":"DESKTOP-FTDK0HP","type":"ping","extra":true}`, "DESKTOP-FTDK0HP"); err == nil {
		t.Fatal("expected unknown-field rejection")
	}
}

func TestIssueQueueDoneReceiptIsReplayedWithoutExecution(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("ANTHARES_ISSUE_QUEUE_STATE_DIR", dir)
	provider := &fakeIssueProvider{}
	item := issueQueueItem{Provider: provider, Source: "1", Job: Job{ID: "dedupe-1", Type: "ping"}}
	cfg := Config{DeviceID: "DESKTOP-FTDK0HP", MaxConcurrent: 1}

	if err := processIssueQueueItem(cfg, item); err != nil {
		t.Fatal(err)
	}
	if provider.acks != 1 || len(provider.results) != 1 || !provider.results[0].OK || provider.results[0].Output != "pong" {
		t.Fatalf("first acknowledgement unexpected: %#v", provider.results)
	}

	if err := processIssueQueueItem(cfg, item); err != nil {
		t.Fatal(err)
	}
	if provider.acks != 2 {
		t.Fatalf("expected stored result replay, got %d acknowledgements", provider.acks)
	}
	if provider.results[1].Output != provider.results[0].Output || provider.results[1].StartedAt != provider.results[0].StartedAt {
		t.Fatalf("stored result was not replayed: %#v", provider.results)
	}
}

func TestIssueQueueStartedReceiptBecomesUncertainWithoutReplay(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("ANTHARES_ISSUE_QUEUE_STATE_DIR", dir)
	started := time.Now().UTC().Add(-time.Minute).Format(time.RFC3339)
	receipt := issueQueueReceipt{JobID: "uncertain-1", State: "started", StartedAt: started, UpdatedAt: started}
	path := filepath.Join(dir, "uncertain-1.json")
	if err := os.WriteFile(path, []byte(`{"job_id":"uncertain-1","state":"started","started_at":"`+started+`","updated_at":"`+started+`"}`), 0600); err != nil {
		t.Fatal(err)
	}
	provider := &fakeIssueProvider{}
	item := issueQueueItem{Provider: provider, Source: "2", Job: Job{ID: "uncertain-1", Type: "ping"}}
	cfg := Config{DeviceID: "DESKTOP-FTDK0HP", MaxConcurrent: 1}
	if err := processIssueQueueItem(cfg, item); err != nil {
		t.Fatal(err)
	}
	if provider.acks != 1 || len(provider.results) != 1 || provider.results[0].OK {
		t.Fatalf("expected uncertain failure result: %#v", provider.results)
	}
	if provider.results[0].Output != "" {
		t.Fatalf("job appears to have been replayed: %#v", provider.results[0])
	}
	_ = receipt
}

func TestSplitASCII(t *testing.T) {
	parts := splitASCII("abcdefghij", 4)
	if len(parts) != 3 || parts[0] != "abcd" || parts[1] != "efgh" || parts[2] != "ij" {
		t.Fatalf("unexpected chunks: %#v", parts)
	}
}
