package main

import (
	"testing"
	"time"
)

func TestControlPollDelay(t *testing.T) {
	tests := []struct {
		name       string
		endpoint   string
		afterError bool
		want       time.Duration
	}{
		{"cf idle", "https://anthares-ara-backup.anthares1.workers.dev", false, 60 * time.Second},
		{"cf fail", "https://anthares-ara-backup.anthares1.workers.dev", true, 60 * time.Second},
		{"cf other", "https://anthares-control.anthares1.workers.dev", false, 60 * time.Second},
		{"cf mixedcase", "https://TEST.Workers.Dev", false, 60 * time.Second},
		{"vercel idle", "https://anthares-ara-vercel-reserve.vercel.app", false, 2 * time.Second},
		{"vercel fail", "https://anthares-ara-vercel-reserve.vercel.app", true, 3 * time.Second},
		{"malformed", "no URL", false, 2 * time.Second},
		{"lookalike", "https://workers.dev.evil.example", false, 2 * time.Second},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := controlPollDelay(tt.endpoint, tt.afterError); got != tt.want {
				t.Errorf("got %s, want %s", got, tt.want)
			}
		})
	}
}
