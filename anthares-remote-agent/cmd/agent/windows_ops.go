package main

import (
    "bytes"
    "context"
    "encoding/json"
    "errors"
    "fmt"
    "os/exec"
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
    if ctx.Err() == context.DeadlineExceeded { return string(b), errors.New("command timed out") }
    if err != nil { return string(b), fmt.Errorf("command exited with code %d", r.ExitCode) }
    return string(b), nil
}

func limitText(s string) string {
    const max = 512 * 1024
    if len(s) > max { return s[:max] + "\n[truncated]" }
    return s
}

func processStartJSON(path, argLine string) (string, error) {
    path = strings.TrimSpace(path)
    if path == "" { return "", errors.New("missing process path") }
    args := []string{}
    if strings.TrimSpace(argLine) != "" {
        // Deliberately simple contract: arguments are passed through cmd's parser.
        // MCP callers should prefer job_start for complex command lines.
        args = []string{"/d", "/s", "/c", fmt.Sprintf("\"%s\" %s", strings.ReplaceAll(path, "\"", ""), argLine)}
        path = "cmd.exe"
    }
    cmd := exec.Command(path, args...)
    if err := cmd.Start(); err != nil { return "", err }
    out, _ := json.Marshal(map[string]any{"pid": cmd.Process.Pid, "status": "started"})
    return string(out), nil
}

func processKillJSON(pidText string) (string, error) {
    pid, err := strconv.Atoi(strings.TrimSpace(pidText))
    if err != nil || pid <= 0 { return "", errors.New("invalid pid") }
    if pid <= 4 { return "", errors.New("refusing to terminate critical system pid") }
    out, err := exec.Command("taskkill", "/PID", strconv.Itoa(pid), "/T", "/F").CombinedOutput()
    if err != nil { return "", fmt.Errorf("taskkill failed: %v: %s", err, strings.TrimSpace(string(out))) }
    b, _ := json.Marshal(map[string]any{"pid":pid,"status":"terminated"})
    return string(b), nil
}

func serviceStatusJSON(ctx context.Context, name string) (string, error) {
    name = strings.TrimSpace(name)
    if name == "" { return "", errors.New("missing service name") }
    script := "$s=Get-Service -Name '" + strings.ReplaceAll(name,"'","''") + "' -ErrorAction Stop; [pscustomobject]@{name=$s.Name;display_name=$s.DisplayName;status=[string]$s.Status;start_type=[string]$s.StartType}|ConvertTo-Json -Compress"
    return run(ctx,"powershell.exe","-NoProfile","-NonInteractive","-Command",script)
}

func serviceControlJSON(ctx context.Context, name string, start bool) (string, error) {
    name = strings.TrimSpace(name)
    if name == "" { return "", errors.New("missing service name") }
    escaped := strings.ReplaceAll(name,"'","''")
    verb := "Start-Service"
    if !start { verb = "Stop-Service" }
    script := "$s=Get-Service -Name '"+escaped+"' -ErrorAction Stop; "+verb+" -InputObject $s -ErrorAction Stop; $s.Refresh(); [pscustomobject]@{name=$s.Name;status=[string]$s.Status}|ConvertTo-Json -Compress"
    return run(ctx,"powershell.exe","-NoProfile","-NonInteractive","-Command",script)
}

func systemInfoJSON(ctx context.Context) (string, error) {
    ps := `$ErrorActionPreference='Stop'; $os=Get-CimInstance Win32_OperatingSystem; $cpu=Get-CimInstance Win32_Processor | Select-Object -First 1; $gpu=Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion; $disks=Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Select-Object DeviceID,Size,FreeSpace; [pscustomobject]@{hostname=$env:COMPUTERNAME;os=$os.Caption;version=$os.Version;arch=$env:PROCESSOR_ARCHITECTURE;cpu=$cpu.Name;ram_bytes=[int64]$os.TotalVisibleMemorySize*1024;free_ram_bytes=[int64]$os.FreePhysicalMemory*1024;last_boot=$os.LastBootUpTime;gpu=$gpu;disks=$disks;agent_version='0.3.0'}|ConvertTo-Json -Depth 5 -Compress`
    return run(ctx,"powershell.exe","-NoProfile","-NonInteractive","-Command",ps)
}
