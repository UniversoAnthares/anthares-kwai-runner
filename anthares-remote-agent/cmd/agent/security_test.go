package main

import (
	"context"
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"path/filepath"
	"strings"
	"testing"
	"time"
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
	if err != nil {
		t.Fatal(err)
	}
	if cfg.MaxConcurrent != 8 {
		t.Fatalf("expected 8, got %d", cfg.MaxConcurrent)
	}

	t.Setenv("ANTHARES_MAX_CONCURRENT", "99")
	cfg, err = loadConfig()
	if err != nil {
		t.Fatal(err)
	}
	if cfg.MaxConcurrent != 4 {
		t.Fatalf("out-of-range value should fall back to 4, got %d", cfg.MaxConcurrent)
	}
}

func TestDispatchShellDisabled(t *testing.T) {
	_, err := dispatch(context.Background(), Config{AllowShell: false}, Job{Type: "shell", Args: map[string]string{"command": "echo test"}})
	if err == nil || !strings.Contains(err.Error(), "shell disabled") {
		t.Fatalf("expected shell disabled error, got %v", err)
	}
}

func TestDispatchRejectsUnsupportedType(t *testing.T) {
	_, err := dispatch(context.Background(), Config{}, Job{Type: "definitely_unknown", Args: map[string]string{}})
	if err == nil || !strings.Contains(err.Error(), "unsupported job type") {
		t.Fatalf("expected unsupported type error, got %v", err)
	}
}

func TestExecutableAllowlistExactPath(t *testing.T) {
	p := filepath.Join(t.TempDir(), "tool.exe")
	t.Setenv("ANTHARES_ALLOWED_EXECUTABLES", p)
	if !executableAllowed(p) {
		t.Fatal("exact allowlisted executable should be accepted")
	}
	if executableAllowed(filepath.Join(filepath.Dir(p), "other.exe")) {
		t.Fatal("different executable must be rejected")
	}
}

func TestServiceAllowlistCaseInsensitive(t *testing.T) {
	t.Setenv("ANTHARES_ALLOWED_SERVICES", "AntharesAgent;Spooler")
	if !serviceAllowed("antharesagent") {
		t.Fatal("service allowlist should be case-insensitive")
	}
	if serviceAllowed("UnlistedService") {
		t.Fatal("unlisted service must be rejected")
	}
}

func TestParseProcessArgsJSON(t *testing.T) {
	args, err := parseProcessArgs(`["--name","value with spaces","& literal"]`)
	if err != nil {
		t.Fatal(err)
	}
	if len(args) != 3 || args[2] != "& literal" {
		t.Fatalf("unexpected args: %#v", args)
	}
	if _, err := parseProcessArgs(`--name value`); err == nil {
		t.Fatal("legacy command-line argument string must be rejected")
	}
}

func TestParseProcessArgsLimits(t *testing.T) {
	items := make([]string, 65)
	for i := range items {
		items[i] = "x"
	}
	raw := `["` + strings.Join(items, `","`) + `"]`
	if _, err := parseProcessArgs(raw); err == nil {
		t.Fatal("more than 64 arguments must be rejected")
	}
}

func signTestPayload(t *testing.T, payload signedJobPayload) (string, ed25519.PrivateKey) {
	t.Helper()
	b, err := json.Marshal(payload)
	if err != nil {
		t.Fatal(err)
	}
	_, priv, err := ed25519.GenerateKey(nil)
	if err != nil {
		t.Fatal(err)
	}
	sig := ed25519.Sign(priv, b)
	return base64.StdEncoding.EncodeToString(sig), priv
}

func makeSignedRemoteJob(t *testing.T, commandID string, scope string, issuedAt int64) (Job, ed25519.PublicKey) {
	t.Helper()
	payload := signedJobPayload{
		JobID:           "rj-test-1234",
		Type:            "remote_job",
		CommandID:       commandID,
		Args:            []string{},
		Cwd:             nil,
		TimeoutSeconds:  30,
		Scope:           scope,
		TokenIdentity:   "test-jti",
		IssuedAt:        issuedAt,
	}
	payloadB, err := json.Marshal(payload)
	if err != nil {
		t.Fatal(err)
	}
	pub, priv, err := ed25519.GenerateKey(nil)
	if err != nil {
		t.Fatal(err)
	}
	sig := ed25519.Sign(priv, payloadB)
	sigObj := map[string]any{"payload": string(payloadB), "sig": base64.StdEncoding.EncodeToString(sig), "issued_at": issuedAt, "expires_at": issuedAt + 60}
	sigB, err := json.Marshal(sigObj)
	if err != nil {
		t.Fatal(err)
	}
	job := Job{
		ID:             "rj-test-1234",
		Type:           "remote_job",
		Args:           map[string]string{"job_signature": string(sigB)},
		TimeoutSeconds: 30,
	}
	return job, pub
}

func TestDispatchRemoteJobNoSignature(t *testing.T) {
	_, err := dispatch(context.Background(), Config{AllowShell: true}, Job{
		Type: "remote_job",
		Args: map[string]string{"command_id": "git.status"},
	})
	if err == nil || !strings.Contains(err.Error(), "signed job metadata") {
		t.Fatalf("expected missing signature error, got %v", err)
	}
}

func TestDispatchRemoteJobInvalidSignature(t *testing.T) {
	_, err := dispatch(context.Background(), Config{AllowShell: true}, Job{
		Type: "remote_job",
		Args: map[string]string{"job_signature": "not-a-valid-signature"},
	})
	if err == nil || !strings.Contains(err.Error(), "invalid job_signature encoding") {
		t.Fatalf("expected invalid signature error, got %v", err)
	}
}

func TestDispatchRemoteJobWrongScope(t *testing.T) {
	job, pub := makeSignedRemoteJob(t, "git.status", "ara.write", time.Now().Unix())
	_, err := dispatch(context.Background(), Config{AllowShell: true, ARAControlPublic: pub}, job)
	if err == nil || !strings.Contains(err.Error(), "scope is not ara.exec") {
		t.Fatalf("expected wrong scope error, got %v", err)
	}
}

func TestDispatchRemoteJobExpiredSignature(t *testing.T) {
	job, pub := makeSignedRemoteJob(t, "git.status", "ara.exec", time.Now().Unix()-120)
	_, err := dispatch(context.Background(), Config{AllowShell: true, ARAControlPublic: pub}, job)
	if err == nil || !strings.Contains(err.Error(), "job signature expired") {
		t.Fatalf("expected expired signature error, got %v", err)
	}
}

func TestDispatchRemoteJobValidSignature(t *testing.T) {
	job, pub := makeSignedRemoteJob(t, "git.status", "ara.exec", time.Now().Unix())
	_, err := dispatch(context.Background(), Config{AllowShell: true, ARAControlPublic: pub}, job)
	if err == nil || strings.Contains(err.Error(), "unsupported job type") {
		t.Fatalf("remote_job should be a supported type, got: %v", err)
	}
}

func TestDispatchShellAndJobStartStillExist(t *testing.T) {
	_, err := dispatch(context.Background(), Config{AllowShell: false}, Job{
		Type: "shell",
		Args: map[string]string{"command": "echo test"},
	})
	if err == nil || !strings.Contains(err.Error(), "shell disabled") {
		t.Fatalf("expected shell disabled error, got %v", err)
	}

	_, err = dispatch(context.Background(), Config{AllowShell: false}, Job{
		Type: "job_start",
		Args: map[string]string{"command": "echo test", "name": "test"},
	})
	if err == nil || !strings.Contains(err.Error(), "shell disabled") {
		t.Fatalf("expected job_start shell disabled error, got %v", err)
	}
}
