package main

import (
    "context"
    "path/filepath"
    "strings"
    "testing"
)

func TestLoadConfigRequiresHTTPS(t *testing.T) {
    t.Setenv("ANTHARES_CONTROL_URL", "http://example.invalid")
    t.Setenv("ANTHARES_DEVICE_TOKEN", "test-token")
    t.Setenv("ANTHARES_DEVICE_ID", "test-device")
    if _, err := loadConfig(); err == nil || !strings.Contains(err.Error(), "HTTPS") {
        t.Fatalf("expected HTTPS validation error, got %v", err)
    }
}

func TestLoadConfigConcurrencyBounds(t *testing.T) {
    t.Setenv("ANTHARES_CONTROL_URL", "https://example.invalid")
    t.Setenv("ANTHARES_DEVICE_TOKEN", "test-token")
    t.Setenv("ANTHARES_DEVICE_ID", "test-device")
    t.Setenv("ANTHARES_MAX_CONCURRENT", "8")
    cfg, err := loadConfig()
    if err != nil { t.Fatal(err) }
    if cfg.MaxConcurrent != 8 { t.Fatalf("expected 8, got %d", cfg.MaxConcurrent) }

    t.Setenv("ANTHARES_MAX_CONCURRENT", "99")
    cfg, err = loadConfig()
    if err != nil { t.Fatal(err) }
    if cfg.MaxConcurrent != 4 { t.Fatalf("out-of-range value should fall back to 4, got %d", cfg.MaxConcurrent) }
}

func TestDispatchShellDisabled(t *testing.T) {
    _, err := dispatch(context.Background(), Config{AllowShell:false}, Job{Type:"shell", Args:map[string]string{"command":"echo test"}})
    if err == nil || !strings.Contains(err.Error(), "shell disabled") { t.Fatalf("expected shell disabled error, got %v", err) }
}

func TestDispatchRejectsUnsupportedType(t *testing.T) {
    _, err := dispatch(context.Background(), Config{}, Job{Type:"definitely_unknown", Args:map[string]string{}})
    if err == nil || !strings.Contains(err.Error(), "unsupported job type") { t.Fatalf("expected unsupported type error, got %v", err) }
}

func TestExecutableAllowlistExactPath(t *testing.T) {
    p := filepath.Join(t.TempDir(), "tool.exe")
    t.Setenv("ANTHARES_ALLOWED_EXECUTABLES", p)
    if !executableAllowed(p) { t.Fatal("exact allowlisted executable should be accepted") }
    if executableAllowed(filepath.Join(filepath.Dir(p), "other.exe")) { t.Fatal("different executable must be rejected") }
}

func TestServiceAllowlistCaseInsensitive(t *testing.T) {
    t.Setenv("ANTHARES_ALLOWED_SERVICES", "AntharesAgent;Spooler")
    if !serviceAllowed("antharesagent") { t.Fatal("service allowlist should be case-insensitive") }
    if serviceAllowed("UnlistedService") { t.Fatal("unlisted service must be rejected") }
}

func TestParseProcessArgsJSON(t *testing.T) {
    args, err := parseProcessArgs(`["--name","value with spaces","& literal"]`)
    if err != nil { t.Fatal(err) }
    if len(args) != 3 || args[2] != "& literal" { t.Fatalf("unexpected args: %#v", args) }
    if _, err := parseProcessArgs(`--name value`); err == nil { t.Fatal("legacy command-line argument string must be rejected") }
}

func TestParseProcessArgsLimits(t *testing.T) {
    items := make([]string, 65)
    for i := range items { items[i] = "x" }
    raw := `["` + strings.Join(items, `","`) + `"]`
    if _, err := parseProcessArgs(raw); err == nil { t.Fatal("more than 64 arguments must be rejected") }
}
