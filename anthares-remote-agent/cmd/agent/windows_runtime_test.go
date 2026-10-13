package main

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"
)

func requireWindows(t *testing.T) {
	t.Helper()
	if runtime.GOOS != "windows" {
		t.Skip("Windows runtime test")
	}
}

func TestWindowsShellCmdStructured(t *testing.T) {
	requireWindows(t)
	out, err := shellExecJSON(context.Background(), "cmd", "echo anthares-runtime")
	if err != nil {
		t.Fatal(err)
	}
	var r commandResult
	if err := json.Unmarshal([]byte(out), &r); err != nil {
		t.Fatal(err)
	}
	if r.ExitCode != 0 || !strings.Contains(strings.ToLower(r.Stdout), "anthares-runtime") {
		t.Fatalf("unexpected shell result: %s", out)
	}
}

func TestWindowsShellExitCode(t *testing.T) {
	requireWindows(t)
	out, err := shellExecJSON(context.Background(), "cmd", "exit /b 7")
	if err == nil {
		t.Fatal("expected non-zero exit error")
	}
	var r commandResult
	if e := json.Unmarshal([]byte(out), &r); e != nil {
		t.Fatal(e)
	}
	if r.ExitCode != 7 {
		t.Fatalf("exit code=%d", r.ExitCode)
	}
}

func TestWindowsProcessInfoSelf(t *testing.T) {
	requireWindows(t)
	out, err := processInfoJSON(context.Background(), itoa(os.Getpid()))
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(out, `"pid"`) {
		t.Fatalf("unexpected process info: %s", out)
	}
}

func TestWindowsServiceList(t *testing.T) {
	requireWindows(t)
	out, err := serviceListJSON(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if strings.TrimSpace(out) == "" {
		t.Fatal("empty service list")
	}
}

func TestWindowsNetworkInfo(t *testing.T) {
	requireWindows(t)
	out, err := networkInfoJSON(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if strings.TrimSpace(out) == "" {
		t.Fatal("empty network info")
	}
}

func TestWindowsTCPConnections(t *testing.T) {
	requireWindows(t)
	out, err := tcpConnectionsJSON(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if strings.TrimSpace(out) == "" {
		t.Fatal("empty TCP output")
	}
}

func TestWindowsScheduledTasks(t *testing.T) {
	requireWindows(t)
	out, err := scheduledTasksJSON(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if strings.TrimSpace(out) == "" {
		t.Fatal("empty scheduled task output")
	}
}

func TestWindowsSystemEventLog(t *testing.T) {
	requireWindows(t)
	out, err := eventLogJSON(context.Background(), "System", "5")
	if err != nil {
		t.Fatal(err)
	}
	if strings.TrimSpace(out) == "" {
		t.Fatal("empty event log output")
	}
}

func TestWindowsEventLogRejectsSecurityByDefault(t *testing.T) {
	requireWindows(t)
	t.Setenv("ANTHARES_ALLOWED_EVENT_LOGS", "")
	if _, err := eventLogJSON(context.Background(), "Security", "5"); err == nil {
		t.Fatal("Security log should require explicit allowlist")
	}
}

func TestWindowsFileACL(t *testing.T) {
	requireWindows(t)
	root := t.TempDir()
	p := filepath.Join(root, "acl.txt")
	if err := os.WriteFile(p, []byte("x"), 0600); err != nil {
		t.Fatal(err)
	}
	out, err := fileACLJSON(context.Background(), Config{AllowedRoots: []string{root}}, p)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(strings.ToLower(out), "owner") {
		t.Fatalf("unexpected ACL output: %s", out)
	}
}

func TestWindowsDetachedJobLifecycle(t *testing.T) {
	requireWindows(t)
	old := os.Getenv("PROGRAMDATA")
	root := t.TempDir()
	t.Setenv("PROGRAMDATA", root)
	defer os.Setenv("PROGRAMDATA", old)

	raw, err := startDetachedJob("echo anthares-job", "runtime-test")
	if err != nil {
		t.Fatal(err)
	}
	var started map[string]any
	if err := json.Unmarshal([]byte(raw), &started); err != nil {
		t.Fatal(err)
	}
	id, _ := started["job_id"].(string)
	if id == "" {
		t.Fatalf("missing job id: %s", raw)
	}

	deadline := time.Now().Add(15 * time.Second)
	for time.Now().Before(deadline) {
		status, err := jobStatusJSON(id, false)
		if err != nil {
			t.Fatal(err)
		}
		if strings.Contains(status, `"status":"exited"`) {
			logs, err := jobLogsJSON(id, -1, 64*1024, 100)
			if err != nil {
				t.Fatal(err)
			}
			if !strings.Contains(strings.ToLower(logs), "anthares-job") {
				t.Fatalf("missing job output: %s", logs)
			}
			return
		}
		time.Sleep(250 * time.Millisecond)
	}
	t.Fatal("detached job did not finish")
}

func TestWindowsClipboardRoundTrip(t *testing.T) {
	requireWindows(t)
	text := "Anthares clipboard Unicode çãõ 漢字"
	if _, err := runWithStdin(context.Background(), text, "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", "$input | Set-Clipboard"); err != nil {
		t.Skipf("runner has no usable interactive clipboard: %v", err)
	}
	out, err := run(context.Background(), "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", "Get-Clipboard -Raw")
	if err != nil {
		t.Skipf("runner has no usable interactive clipboard: %v", err)
	}
	if !strings.Contains(out, "Anthares clipboard Unicode") {
		t.Fatalf("clipboard mismatch: %q", out)
	}
}

func TestWindowsScreenshotProbe(t *testing.T) {
	requireWindows(t)
	out, err := screenshotBase64(context.Background(), "0")
	if err != nil {
		t.Skipf("hosted runner has no interactive desktop: %v", err)
	}
	if len(strings.TrimSpace(out)) < 16 {
		t.Fatal("empty screenshot")
	}
}

func itoa(v int) string {
	const digits = "0123456789"
	if v == 0 {
		return "0"
	}
	b := make([]byte, 0, 20)
	for v > 0 {
		b = append(b, digits[v%10])
		v /= 10
	}
	for i, j := 0, len(b)-1; i < j; i, j = i+1, j-1 {
		b[i], b[j] = b[j], b[i]
	}
	return string(b)
}
