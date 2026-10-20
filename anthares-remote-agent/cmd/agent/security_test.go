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

func makeSignedRemoteJob(t *testing.T, commandID string, scope string, issuedAt int64, jobID string) (Job, ed25519.PublicKey) {
	t.Helper()
	if jobID == "" {
		jobID = "rj-test-default"
	}
	payload := signedJobPayload{
		JobID:           jobID,
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
	signedBytes := append([]byte("ara-remote-job-v1\n"), payloadB...)
	pub, priv, err := ed25519.GenerateKey(nil)
	if err != nil {
		t.Fatal(err)
	}
	sig := ed25519.Sign(priv, signedBytes)
	sigObj := map[string]any{"payload": string(payloadB), "sig": base64.StdEncoding.EncodeToString(sig), "issued_at": issuedAt, "expires_at": issuedAt + 60}
	sigB, err := json.Marshal(sigObj)
	if err != nil {
		t.Fatal(err)
	}
	job := Job{
		ID:             jobID,
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
	job, pub := makeSignedRemoteJob(t, "git.status", "ara.write", time.Now().Unix(), "rj-wrong-scope")
	seenDir := t.TempDir()
	t.Setenv("ANTHARES_SEEN_JOBS_DIR", seenDir)
	_, err := dispatch(context.Background(), Config{AllowShell: true, ARAControlPublic: pub}, job)
	if err == nil || !strings.Contains(err.Error(), "scope is not ara.exec") {
		t.Fatalf("expected wrong scope error, got %v", err)
	}
}

func TestDispatchRemoteJobExpiredSignature(t *testing.T) {
	job, pub := makeSignedRemoteJob(t, "git.status", "ara.exec", time.Now().Unix()-120, "rj-expired")
	seenDir := t.TempDir()
	t.Setenv("ANTHARES_SEEN_JOBS_DIR", seenDir)
	_, err := dispatch(context.Background(), Config{AllowShell: true, ARAControlPublic: pub}, job)
	if err == nil || !strings.Contains(err.Error(), "job signature issued too long ago") {
		t.Fatalf("expected expired signature error, got %v", err)
	}
}

func TestDispatchRemoteJobValidSignature(t *testing.T) {
	job, pub := makeSignedRemoteJob(t, "git.status", "ara.exec", time.Now().Unix(), "rj-valid")
	seenDir := t.TempDir()
	t.Setenv("ANTHARES_SEEN_JOBS_DIR", seenDir)
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

func TestDispatchRemoteJobRejectsOtherContextSignature(t *testing.T) {
	// Assinatura válida de outro contexto (service-signing): sem o prefixo de domínio
	pub, priv, err := ed25519.GenerateKey(nil)
	if err != nil {
		t.Fatal(err)
	}
	seenDir := t.TempDir()
	t.Setenv("ANTHARES_SEEN_JOBS_DIR", seenDir)
	payload := signedJobPayload{
		JobID:           "rj-other-context",
		Type:            "remote_job",
		CommandID:       "git.status",
		Args:            []string{},
		Cwd:             nil,
		TimeoutSeconds:  30,
		Scope:           "ara.exec",
		TokenIdentity:   "other-jti",
		IssuedAt:        time.Now().Unix(),
	}
	payloadB, err := json.Marshal(payload)
	if err != nil {
		t.Fatal(err)
	}
	sig := ed25519.Sign(priv, payloadB) // sem prefixo "ara-remote-job-v1\n"
	sigObj := map[string]any{"payload": string(payloadB), "sig": base64.StdEncoding.EncodeToString(sig), "issued_at": payload.IssuedAt, "expires_at": payload.IssuedAt + 60}
	sigB, err := json.Marshal(sigObj)
	if err != nil {
		t.Fatal(err)
	}
	job := Job{
		ID:             "rj-other-context",
		Type:           "remote_job",
		Args:           map[string]string{"job_signature": string(sigB)},
		TimeoutSeconds: 30,
	}
	_, err = dispatch(context.Background(), Config{AllowShell: true, ARAControlPublic: pub}, job)
	if err == nil || !strings.Contains(err.Error(), "job signature verification failed") {
		t.Fatalf("expected signature from other context to be rejected, got %v", err)
	}
}

func TestDispatchRemoteJobReplayRejected(t *testing.T) {
	job, pub := makeSignedRemoteJob(t, "git.status", "ara.exec", time.Now().Unix(), "rj-replay")
	seenDir := t.TempDir()
	t.Setenv("ANTHARES_SEEN_JOBS_DIR", seenDir)
	// Primeira execução: assinatura válida, não é replay
	_, err1 := dispatch(context.Background(), Config{AllowShell: true, ARAControlPublic: pub}, job)
	if err1 != nil && strings.Contains(err1.Error(), "job_id already executed") {
		t.Fatalf("first call should not be rejected as replay, got %v", err1)
	}
	// Segunda execução com mesmo job_id: deve ser rejeitada por replay
	_, err2 := dispatch(context.Background(), Config{AllowShell: true, ARAControlPublic: pub}, job)
	if err2 == nil || !strings.Contains(err2.Error(), "job_id already executed") {
		t.Fatalf("expected replay rejection on second call, got %v", err2)
	}
}

func TestParseHandlerOutputPendingApproval(t *testing.T) {
	// Saida real do handler local: ok=false, error=pending_approval, exit_code 0
	out := `{"ok":false,"error":"pending_approval","exit_code":0,"output":"","command_id":"git.status"}`
	ok, err := parseHandlerOutput(out)
	if ok {
		t.Fatal("ok=false deve ser tratado como falha do job")
	}
	if err == nil || err.Error() != "pending_approval" {
		t.Fatalf("expected pending_approval error preserved, got %v", err)
	}
}

func TestParseHandlerOutputRemoteJobDisabled(t *testing.T) {
	out := `{"ok":false,"error":"remote_job_disabled","exit_code":0}`
	ok, err := parseHandlerOutput(out)
	if ok {
		t.Fatal("remote_job_disabled deve ser falha do job")
	}
	if err == nil || err.Error() != "remote_job_disabled" {
		t.Fatalf("expected remote_job_disabled error preserved, got %v", err)
	}
}

func TestParseHandlerOutputSuccess(t *testing.T) {
	out := `{"ok":true,"exit_code":0,"output":"ok"}`
	ok, err := parseHandlerOutput(out)
	if !ok || err != nil {
		t.Fatalf("expected success, got ok=%v err=%v", ok, err)
	}
}

func TestDispatchRemoteJobClockTolerance(t *testing.T) {
	seenDir := t.TempDir()
	t.Setenv("ANTHARES_SEEN_JOBS_DIR", seenDir)
	// issued_at dentro da margem (60s) deve ser aceito (não rejeitado por assinatura)
	job, pub := makeSignedRemoteJob(t, "git.status", "ara.exec", time.Now().Unix(), "rj-clock-now")
	_, err := dispatch(context.Background(), Config{AllowShell: true, ARAControlPublic: pub}, job)
	if err != nil && (strings.Contains(err.Error(), "job signature") || strings.Contains(err.Error(), "job_id already executed")) {
		t.Fatalf("current-time signature should pass validation, got %v", err)
	}

	// issued_at com 59s de diferença deve ser aceito (dentro da janela de 60s)
	job2, pub2 := makeSignedRemoteJob(t, "git.status", "ara.exec", time.Now().Unix()-59, "rj-clock-59s")
	_, err2 := dispatch(context.Background(), Config{AllowShell: true, ARAControlPublic: pub2}, job2)
	if err2 != nil && (strings.Contains(err2.Error(), "job signature") || strings.Contains(err2.Error(), "job_id already executed")) {
		t.Fatalf("59s-old signature should pass validation, got %v", err2)
	}

	// issued_at com 61s de diferença deve ser rejeitado (fora da janela de 60s)
	job3, pub3 := makeSignedRemoteJob(t, "git.status", "ara.exec", time.Now().Unix()-61, "rj-clock-61s")
	_, err3 := dispatch(context.Background(), Config{AllowShell: true, ARAControlPublic: pub3}, job3)
	if err3 == nil || !strings.Contains(err3.Error(), "job signature issued too long ago") {
		t.Fatalf("expected issued-too-long-ago error for 61s-old signature, got %v", err3)
	}
}
