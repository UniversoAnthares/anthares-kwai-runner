package main

import (
	"bufio"
	"context"
	"crypto/rand"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

type detachedJobMeta struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	Command   string `json:"command,omitempty"`
	PID       int    `json:"pid"`
	StartedAt string `json:"started_at"`
	JobDir    string `json:"job_dir"`
}

func jobsRoot() string {
	base := os.Getenv("PROGRAMDATA")
	if base == "" {
		base = os.TempDir()
	}
	return filepath.Join(base, "AntharesRemoteAgent", "jobs")
}

func newJobID() (string, error) {
	b := make([]byte, 8)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return hex.EncodeToString(b), nil
}

func fileStatJSON(cfg Config, path string) (string, error) {
	p, err := safePath(cfg, path)
	if err != nil {
		return "", err
	}
	st, err := os.Stat(p)
	if err != nil {
		return "", err
	}
	out := map[string]any{
		"path": p, "name": st.Name(), "size": st.Size(), "is_dir": st.IsDir(),
		"mode": st.Mode().String(), "modified_at": st.ModTime().UTC().Format(time.RFC3339Nano),
	}
	b, _ := json.Marshal(out)
	return string(b), nil
}

func fileListJSON(cfg Config, path string) (string, error) {
	p, err := safePath(cfg, path)
	if err != nil {
		return "", err
	}
	entries, err := os.ReadDir(p)
	if err != nil {
		return "", err
	}
	if len(entries) > 1000 {
		entries = entries[:1000]
	}
	out := make([]map[string]any, 0, len(entries))
	for _, e := range entries {
		item := map[string]any{"name": e.Name(), "is_dir": e.IsDir()}
		if info, er := e.Info(); er == nil {
			item["size"] = info.Size()
			item["mode"] = info.Mode().String()
			item["modified_at"] = info.ModTime().UTC().Format(time.RFC3339Nano)
		}
		out = append(out, item)
	}
	b, _ := json.Marshal(out)
	return string(b), nil
}

func fileReadChunk(cfg Config, path string, offset, length int64) (string, error) {
	p, err := safePath(cfg, path)
	if err != nil {
		return "", err
	}
	if offset < 0 {
		return "", errors.New("offset must be >= 0")
	}
	if length <= 0 || length > 512*1024 {
		length = 512 * 1024
	}
	f, err := os.Open(p)
	if err != nil {
		return "", err
	}
	defer f.Close()
	st, err := f.Stat()
	if err != nil {
		return "", err
	}
	if st.IsDir() {
		return "", errors.New("path is a directory")
	}
	if offset > st.Size() {
		offset = st.Size()
	}
	buf := make([]byte, length)
	n, er := f.ReadAt(buf, offset)
	if er != nil && n == 0 && offset < st.Size() {
		return "", er
	}
	out := map[string]any{
		"path": p, "offset": offset, "next_offset": offset + int64(n), "size": st.Size(),
		"eof": offset+int64(n) >= st.Size(), "base64": base64.StdEncoding.EncodeToString(buf[:n]),
	}
	b, _ := json.Marshal(out)
	return string(b), nil
}

func fileWriteChunk(cfg Config, path string, offset int64, dataB64 string, truncate bool) (string, error) {
	p, err := safePath(cfg, path)
	if err != nil {
		return "", err
	}
	if offset < 0 {
		return "", errors.New("offset must be >= 0")
	}
	data, err := base64.StdEncoding.DecodeString(dataB64)
	if err != nil {
		return "", err
	}
	if len(data) > 512*1024 {
		return "", errors.New("chunk exceeds 512 KiB")
	}
	if err := os.MkdirAll(filepath.Dir(p), 0700); err != nil {
		return "", err
	}
	flags := os.O_CREATE | os.O_WRONLY
	if truncate && offset == 0 {
		flags |= os.O_TRUNC
	}
	f, err := os.OpenFile(p, flags, 0600)
	if err != nil {
		return "", err
	}
	defer f.Close()
	n, err := f.WriteAt(data, offset)
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("wrote %d bytes at offset %d", n, offset), nil
}

func screenshotBase64(ctx context.Context, display string) (string, error) {
	// Screenshot the requested display (0-based) or all displays. The agent must run in an interactive user session.
	if display == "" {
		display = "0"
	}
	ps := `$ErrorActionPreference='Stop'; Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; ` +
		`$d='` + strings.ReplaceAll(display, "'", "''") + `'; ` +
		`if($d -eq 'all'){$b=[System.Windows.Forms.SystemInformation]::VirtualScreen}else{$i=[int]$d;$screens=[System.Windows.Forms.Screen]::AllScreens;if($i -lt 0 -or $i -ge $screens.Count){throw 'display index out of range'};$b=$screens[$i].Bounds}; ` +
		`$bmp=New-Object System.Drawing.Bitmap($b.Width,$b.Height);$g=[System.Drawing.Graphics]::FromImage($bmp);$g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size);` +
		`$ms=New-Object System.IO.MemoryStream;$bmp.Save($ms,[System.Drawing.Imaging.ImageFormat]::Jpeg);$g.Dispose();$bmp.Dispose();` +
		`$bytes=$ms.ToArray();$ms.Dispose();[Convert]::ToBase64String($bytes)`
	out, err := run(ctx, "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps)
	if err != nil {
		return out, err
	}
	out = strings.TrimSpace(out)
	if len(out) < 16 {
		return "", errors.New("empty screenshot")
	}
	return out, nil
}

func startDetachedJob(command, name string) (string, error) {
	command = strings.TrimSpace(command)
	if command == "" {
		return "", errors.New("missing command")
	}
	id, err := newJobID()
	if err != nil {
		return "", err
	}
	root := jobsRoot()
	if err := os.MkdirAll(root, 0700); err != nil {
		return "", err
	}
	dir := filepath.Join(root, id)
	if err := os.MkdirAll(dir, 0700); err != nil {
		return "", err
	}
	if name == "" {
		name = "job-" + id
	}
	logPath := filepath.Join(dir, "output.log")
	exitPath := filepath.Join(dir, "exit.txt")
	wrapperPath := filepath.Join(dir, "run.ps1")
	cmdB64 := base64.StdEncoding.EncodeToString([]byte(command))
	wrapper := "$ErrorActionPreference='Continue'\r\n" +
		"$cmd=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('" + cmdB64 + "'))\r\n" +
		"& cmd.exe /d /s /c $cmd *>> '" + strings.ReplaceAll(logPath, "'", "''") + "'\r\n" +
		"$ec=$LASTEXITCODE\r\nSet-Content -Encoding ASCII -Path '" + strings.ReplaceAll(exitPath, "'", "''") + "' -Value $ec\r\nexit $ec\r\n"
	if err := os.WriteFile(wrapperPath, []byte(wrapper), 0600); err != nil {
		return "", err
	}
	ps := `$p=Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','` + strings.ReplaceAll(wrapperPath, "'", "''") + `' -PassThru; $p.Id`
	out, err := exec.Command("powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps).CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("start failed: %v: %s", err, strings.TrimSpace(string(out)))
	}
	pid, err := strconv.Atoi(strings.TrimSpace(string(out)))
	if err != nil {
		return "", fmt.Errorf("invalid pid: %s", strings.TrimSpace(string(out)))
	}
	meta := detachedJobMeta{ID: id, Name: name, Command: command, PID: pid, StartedAt: time.Now().UTC().Format(time.RFC3339Nano), JobDir: dir}
	b, _ := json.Marshal(meta)
	_ = os.WriteFile(filepath.Join(dir, "meta.json"), b, 0600)
	res := map[string]any{"job_id": id, "name": name, "pid": pid, "status": "running", "started_at": meta.StartedAt}
	rb, _ := json.Marshal(res)
	return string(rb), nil
}

func loadJobMeta(id string) (detachedJobMeta, error) {
	var m detachedJobMeta
	if len(id) != 16 {
		return m, errors.New("invalid job id")
	}
	b, err := os.ReadFile(filepath.Join(jobsRoot(), id, "meta.json"))
	if err != nil {
		return m, err
	}
	if err := json.Unmarshal(b, &m); err != nil {
		return m, err
	}
	return m, nil
}

func processRunning(pid int) bool {
	out, _ := exec.Command("tasklist", "/FI", fmt.Sprintf("PID eq %d", pid), "/FO", "CSV", "/NH").CombinedOutput()
	s := strings.TrimSpace(string(out))
	return s != "" && !strings.Contains(strings.ToLower(s), "no tasks") && !strings.Contains(strings.ToLower(s), "nenhuma tarefa")
}

func jobStatusJSON(id string, includeCommand bool) (string, error) {
	m, err := loadJobMeta(id)
	if err != nil {
		return "", err
	}
	status := "running"
	var exitCode any = nil
	exitPath := filepath.Join(m.JobDir, "exit.txt")
	if b, er := os.ReadFile(exitPath); er == nil {
		status = "exited"
		if n, er2 := strconv.Atoi(strings.TrimSpace(string(b))); er2 == nil {
			exitCode = n
		}
	} else if !processRunning(m.PID) {
		status = "unknown"
	}
	st, _ := os.Stat(filepath.Join(m.JobDir, "output.log"))
	var logSize int64
	if st != nil {
		logSize = st.Size()
	}
	out := map[string]any{"job_id": m.ID, "name": m.Name, "pid": m.PID, "status": status, "exit_code": exitCode, "started_at": m.StartedAt, "log_size": logSize}
	if includeCommand {
		out["command"] = m.Command
	}
	b, _ := json.Marshal(out)
	return string(b), nil
}

func jobListJSON(includeCommand bool, limit int) (string, error) {
	if limit <= 0 || limit > 100 {
		limit = 20
	}
	entries, err := os.ReadDir(jobsRoot())
	if err != nil {
		if os.IsNotExist(err) {
			return "[]", nil
		}
		return "", err
	}
	out := make([]json.RawMessage, 0)
	for i := len(entries) - 1; i >= 0 && len(out) < limit; i-- {
		if !entries[i].IsDir() {
			continue
		}
		s, er := jobStatusJSON(entries[i].Name(), includeCommand)
		if er == nil {
			out = append(out, json.RawMessage(s))
		}
	}
	b, _ := json.Marshal(out)
	return string(b), nil
}

func jobLogsJSON(id string, offset int64, maxBytes int, tailLines int) (string, error) {
	m, err := loadJobMeta(id)
	if err != nil {
		return "", err
	}
	p := filepath.Join(m.JobDir, "output.log")
	b, err := os.ReadFile(p)
	if err != nil {
		if os.IsNotExist(err) {
			b = []byte{}
		} else {
			return "", err
		}
	}
	if maxBytes <= 0 || maxBytes > 256*1024 {
		maxBytes = 256 * 1024
	}
	var chunk []byte
	var next int64
	if offset >= 0 {
		if offset > int64(len(b)) {
			offset = int64(len(b))
		}
		end := offset + int64(maxBytes)
		if end > int64(len(b)) {
			end = int64(len(b))
		}
		chunk = b[offset:end]
		next = end
	} else {
		if tailLines <= 0 {
			tailLines = 200
		}
		scanner := bufio.NewScanner(strings.NewReader(string(b)))
		lines := []string{}
		for scanner.Scan() {
			lines = append(lines, scanner.Text())
		}
		if len(lines) > tailLines {
			lines = lines[len(lines)-tailLines:]
		}
		text := strings.Join(lines, "\n")
		if len(text) > maxBytes {
			text = text[len(text)-maxBytes:]
		}
		chunk = []byte(text)
		next = int64(len(b))
	}
	out := map[string]any{"job_id": id, "offset": offset, "next_offset": next, "log_size": len(b), "text": string(chunk)}
	rb, _ := json.Marshal(out)
	return string(rb), nil
}

func jobCancelJSON(id string) (string, error) {
	m, err := loadJobMeta(id)
	if err != nil {
		return "", err
	}
	if processRunning(m.PID) {
		out, er := exec.Command("taskkill", "/PID", strconv.Itoa(m.PID), "/T", "/F").CombinedOutput()
		if er != nil {
			return "", fmt.Errorf("taskkill failed: %v: %s", er, strings.TrimSpace(string(out)))
		}
	}
	s, _ := jobStatusJSON(id, false)
	return s, nil
}

