package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

type agentHealth struct {
	OK                bool     `json:"ok"`
	Protocol          string   `json:"protocol"`
	PID               int      `json:"pid"`
	Hostname          string   `json:"hostname"`
	Username          string   `json:"username,omitempty"`
	OS                string   `json:"os"`
	Arch              string   `json:"arch"`
	DeviceID          string   `json:"device_id"`
	WorkRoot          string   `json:"work_root,omitempty"`
	HTTPControl       bool     `json:"http_control"`
	ShellEnabled      bool     `json:"shell_enabled"`
	QueueConfigured   bool     `json:"queue_configured"`
	QueueProviders    []string `json:"queue_providers"`
	QueueStateDir     string   `json:"queue_state_dir,omitempty"`
	QueueReceiptCount int      `json:"queue_receipt_count"`
	CheckedAt         string   `json:"checked_at"`
}

func agentHealthJSON(cfg Config) (string, error) {
	providerNames := make([]string, 0, 2)
	for _, p := range issueQueueProviders() {
		providerNames = append(providerNames, p.Name())
	}
	stateDir, _ := issueQueueStateDir()
	receipts := 0
	if stateDir != "" {
		if entries, err := os.ReadDir(stateDir); err == nil {
			for _, entry := range entries {
				if !entry.IsDir() && strings.EqualFold(filepath.Ext(entry.Name()), ".json") {
					receipts++
				}
			}
		}
	}
	h := agentHealth{
		OK:                true,
		Protocol:          "anthares-remote-agent/0.4",
		PID:               os.Getpid(),
		Hostname:          hostname(),
		Username:          os.Getenv("USERNAME"),
		OS:                runtime.GOOS,
		Arch:              runtime.GOARCH,
		DeviceID:          cfg.DeviceID,
		WorkRoot:          strings.TrimSpace(os.Getenv("ANTHARES_WORK_ROOT")),
		HTTPControl:       strings.TrimSpace(cfg.ControlURL) != "",
		ShellEnabled:      cfg.AllowShell,
		QueueConfigured:   issueQueueConfigured(),
		QueueProviders:    providerNames,
		QueueStateDir:     stateDir,
		QueueReceiptCount: receipts,
		CheckedAt:         time.Now().UTC().Format(time.RFC3339),
	}
	b, err := json.Marshal(h)
	return string(b), err
}
