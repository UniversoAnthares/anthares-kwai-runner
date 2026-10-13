package main

import (
	"encoding/json"
	"runtime"
	"testing"
)

func TestExecuteJobPreservesStructuredFailure(t *testing.T) {
	if runtime.GOOS != "windows" {
		t.Skip("Windows command interpreter required")
	}
	cfg := Config{AllowShell: true}
	job := Job{
		ID:   "structured-failure",
		Type: "shell",
		Args: map[string]string{
			"shell":   "cmd",
			"command": "echo diagnostic-out & echo diagnostic-err 1>&2 & exit /b 7",
		},
	}
	result := executeJob(cfg, job)
	if result.OK {
		t.Fatal("nonzero exit must report failure")
	}
	if result.Error == "" || result.Output == "" {
		t.Fatalf("error and output must be preserved: %#v", result)
	}
	var got commandResult
	if err := json.Unmarshal([]byte(result.Output), &got); err != nil {
		t.Fatalf("structured output is not JSON: %v", err)
	}
	if got.ExitCode != 7 {
		t.Fatalf("exit code = %d, want 7", got.ExitCode)
	}
	if got.Stdout == "" || got.Stderr == "" {
		t.Fatalf("stdout and stderr must both be present: %#v", got)
	}
}
