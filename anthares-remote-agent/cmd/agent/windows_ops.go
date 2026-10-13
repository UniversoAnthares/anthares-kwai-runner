package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
)

type commandResult struct {
	Stdout   string `json:"stdout"`
	Stderr   string `json:"stderr"`
	ExitCode int    `json:"exit_code"`
	TimedOut bool   `json:"timed_out"`
}

func shellExecJSON(ctx context.Context, shell, command string) (string, error) {
	var name string
	var args []string
	switch shell {
	case "", "powershell":
		name = "powershell.exe"
		args = []string{"-NoProfile", "-NonInteractive", "-Command", command}
	case "cmd":
		name = "cmd.exe"
		args = []string{"/d", "/s", "/c", command}
	default:
		return "", fmt.Errorf("unsupported shell %q", shell)
	}
	cmd := exec.CommandContext(ctx, name, args...)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	err := cmd.Run()
	r := commandResult{Stdout: limitText(stdout.String()), Stderr: limitText(stderr.String())}
	if ctx.Err() == context.DeadlineExceeded {
		r.TimedOut = true
		r.ExitCode = -1
	} else if err == nil {
		r.ExitCode = 0
	} else if ee, ok := err.(*exec.ExitError); ok {
		r.ExitCode = ee.ExitCode()
	} else {
		r.ExitCode = -1
	}
	b, _ := json.Marshal(r)
	if ctx.Err() == context.DeadlineExceeded {
		return string(b), errors.New("command timed out")
	}
	if err != nil {
		return string(b), fmt.Errorf("command exited with code %d", r.ExitCode)
	}
	return string(b), nil
}

func limitText(s string) string {
	const max = 512 * 1024
	if len(s) > max {
		return s[:max] + "\n[truncated]"
	}
	return s
}

func envAllowlist(name string) []string {
	var out []string
	for _, item := range strings.Split(os.Getenv(name), ";") {
		item = strings.TrimSpace(item)
		if item != "" {
			out = append(out, item)
		}
	}
	return out
}

func executableAllowed(path string) bool {
	abs, err := filepath.Abs(path)
	if err != nil {
		return false
	}
	abs = strings.ToLower(filepath.Clean(abs))
	for _, allowed := range envAllowlist("ANTHARES_ALLOWED_EXECUTABLES") {
		a, err := filepath.Abs(allowed)
		if err == nil && strings.EqualFold(filepath.Clean(a), abs) {
			return true
		}
	}
	return false
}

func serviceAllowed(name string) bool {
	for _, allowed := range envAllowlist("ANTHARES_ALLOWED_SERVICES") {
		if strings.EqualFold(allowed, strings.TrimSpace(name)) {
			return true
		}
	}
	return false
}

func parseProcessArgs(argsJSON string) ([]string, error) {
	if strings.TrimSpace(argsJSON) == "" {
		return nil, nil
	}
	var args []string
	if err := json.Unmarshal([]byte(argsJSON), &args); err != nil {
		return nil, errors.New("args_json must be a JSON array of strings")
	}
	if len(args) > 64 {
		return nil, errors.New("too many process arguments")
	}
	total := 0
	for _, arg := range args {
		total += len(arg)
		if len(arg) > 8192 || total > 32768 {
			return nil, errors.New("process arguments exceed limit")
		}
	}
	return args, nil
}

func processStartJSON(path, argsJSON string) (string, error) {
	path = strings.TrimSpace(path)
	if path == "" {
		return "", errors.New("missing process path")
	}
	if !executableAllowed(path) {
		return "", errors.New("executable is not authorized")
	}
	args, err := parseProcessArgs(argsJSON)
	if err != nil {
		return "", err
	}
	cmd := exec.Command(path, args...)
	if err := cmd.Start(); err != nil {
		return "", err
	}
	pid := cmd.Process.Pid
	_ = cmd.Process.Release()
	out, _ := json.Marshal(map[string]any{"pid": pid, "status": "started"})
	return string(out), nil
}

func processKillJSON(pidText string) (string, error) {
	pid, err := strconv.Atoi(strings.TrimSpace(pidText))
	if err != nil || pid <= 0 {
		return "", errors.New("invalid pid")
	}
	if pid <= 4 {
		return "", errors.New("refusing to terminate critical system pid")
	}

	ps := fmt.Sprintf("(Get-CimInstance Win32_Process -Filter \"ProcessId=%d\" -ErrorAction Stop).ExecutablePath", pid)
	raw, err := exec.Command("powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps).CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("cannot identify process: %v", err)
	}
	path := strings.TrimSpace(string(raw))
	if path == "" || !executableAllowed(path) {
		return "", errors.New("process executable is not authorized")
	}

	out, err := exec.Command("taskkill", "/PID", strconv.Itoa(pid), "/T", "/F").CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("taskkill failed: %v: %s", err, strings.TrimSpace(string(out)))
	}
	b, _ := json.Marshal(map[string]any{"pid": pid, "status": "terminated"})
	return string(b), nil
}

func serviceStatusJSON(ctx context.Context, name string) (string, error) {
	name = strings.TrimSpace(name)
	if name == "" {
		return "", errors.New("missing service name")
	}
	script := "$s=Get-Service -Name '" + strings.ReplaceAll(name, "'", "''") + "' -ErrorAction Stop; [pscustomobject]@{name=$s.Name;display_name=$s.DisplayName;status=[string]$s.Status;start_type=[string]$s.StartType}|ConvertTo-Json -Compress"
	return run(ctx, "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script)
}

func serviceControlJSON(ctx context.Context, name string, start bool) (string, error) {
	name = strings.TrimSpace(name)
	if name == "" {
		return "", errors.New("missing service name")
	}
	if !serviceAllowed(name) {
		return "", errors.New("service is not authorized")
	}
	escaped := strings.ReplaceAll(name, "'", "''")
	verb := "Start-Service"
	if !start {
		verb = "Stop-Service"
	}
	script := "$s=Get-Service -Name '" + escaped + "' -ErrorAction Stop; " + verb + " -InputObject $s -ErrorAction Stop; $s.Refresh(); [pscustomobject]@{name=$s.Name;status=[string]$s.Status}|ConvertTo-Json -Compress"
	return run(ctx, "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script)
}

func systemInfoJSON(ctx context.Context) (string, error) {
	ps := `$ErrorActionPreference='Stop'; $os=Get-CimInstance Win32_OperatingSystem; $cpu=Get-CimInstance Win32_Processor | Select-Object -First 1; $gpu=Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion; $disks=Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Select-Object DeviceID,Size,FreeSpace; [pscustomobject]@{hostname=$env:COMPUTERNAME;os=$os.Caption;version=$os.Version;arch=$env:PROCESSOR_ARCHITECTURE;cpu=$cpu.Name;ram_bytes=[int64]$os.TotalVisibleMemorySize*1024;free_ram_bytes=[int64]$os.FreePhysicalMemory*1024;last_boot=$os.LastBootUpTime;gpu=$gpu;disks=$disks;agent_version='0.3.0'}|ConvertTo-Json -Depth 5 -Compress`
	return run(ctx, "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps)
}

