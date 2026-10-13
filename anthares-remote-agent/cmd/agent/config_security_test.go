package main

import (
	"os"
	"strings"
	"testing"
)

func TestLoadConfigRejectsUnsafeControlURL(t *testing.T) {
	keys := []string{"ANTHARES_CONTROL_URL", "ANTHARES_DEVICE_TOKEN", "ANTHARES_DEVICE_ID"}
	original := make(map[string]string)
	for _, k := range keys {
		original[k] = os.Getenv(k)
	}
	defer func() {
		for _, k := range keys {
			_ = os.Setenv(k, original[k])
		}
	}()
	_ = os.Setenv("ANTHARES_DEVICE_TOKEN", "test")
	_ = os.Setenv("ANTHARES_DEVICE_ID", "test-device")
	for _, raw := range []string{"http://example.org", "https://user:pass@example.org", "https://example.org/path", "https://example.org/?x=1", "https://example.org/#fragment", "https://", "not-a-url"} {
		_ = os.Setenv("ANTHARES_CONTROL_URL", raw)
		if _, err := loadConfig(); err == nil {
			t.Errorf("unsafe control URL accepted: %q", raw)
		}
	}
	_ = os.Setenv("ANTHARES_CONTROL_URL", "https://example.org")
	cfg, err := loadConfig()
	if err != nil || !strings.HasPrefix(cfg.ControlURL, "https://") {
		t.Fatalf("valid HTTPS origin rejected: %v", err)
	}
}

