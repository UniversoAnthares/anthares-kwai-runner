package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strconv"
	"strings"
)

func processInfoJSON(ctx context.Context, pidText string) (string, error) {
	pid, err := strconv.Atoi(strings.TrimSpace(pidText))
	if err != nil || pid <= 0 {
		return "", errors.New("invalid pid")
	}
	ps := fmt.Sprintf(`$p=Get-CimInstance Win32_Process -Filter "ProcessId=%d" -ErrorAction Stop; [pscustomobject]@{pid=$p.ProcessId;parent_pid=$p.ParentProcessId;name=$p.Name;executable_path=$p.ExecutablePath;created_at=$p.CreationDate;working_set_bytes=$p.WorkingSetSize}|ConvertTo-Json -Compress`, pid)
	return run(ctx, "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps)
}

func serviceListJSON(ctx context.Context) (string, error) {
	ps := `Get-Service | Sort-Object Name | Select-Object -First 2000 Name,DisplayName,@{n='Status';e={[string]$_.Status}},@{n='StartType';e={[string]$_.StartType}} | ConvertTo-Json -Compress`
	return run(ctx, "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps)
}

func networkInfoJSON(ctx context.Context) (string, error) {
	ps := `$items=Get-NetIPConfiguration | ForEach-Object {[pscustomobject]@{interface_alias=$_.InterfaceAlias;interface_description=$_.InterfaceDescription;ipv4=@($_.IPv4Address|ForEach-Object IPAddress);ipv6=@($_.IPv6Address|ForEach-Object IPAddress);ipv4_gateway=@($_.IPv4DefaultGateway|ForEach-Object NextHop);dns=@($_.DNSServer.ServerAddresses)}}; $items|ConvertTo-Json -Depth 5 -Compress`
	return run(ctx, "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps)
}

func tcpConnectionsJSON(ctx context.Context) (string, error) {
	ps := `Get-NetTCPConnection -ErrorAction Stop | Select-Object -First 2000 LocalAddress,LocalPort,RemoteAddress,RemotePort,@{n='State';e={[string]$_.State}},OwningProcess | ConvertTo-Json -Compress`
	return run(ctx, "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps)
}

func scheduledTasksJSON(ctx context.Context) (string, error) {
	ps := `Get-ScheduledTask | Sort-Object TaskPath,TaskName | Select-Object -First 2000 TaskName,TaskPath,@{n='State';e={[string]$_.State}} | ConvertTo-Json -Compress`
	return run(ctx, "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps)
}

func eventLogAllowed(name string) bool {
	name = strings.TrimSpace(name)
	if name == "" {
		return false
	}
	allowed := envAllowlist("ANTHARES_ALLOWED_EVENT_LOGS")
	if len(allowed) == 0 {
		allowed = []string{"System", "Application"}
	}
	for _, item := range allowed {
		if strings.EqualFold(item, name) {
			return true
		}
	}
	return false
}

func eventLogJSON(ctx context.Context, name, maxText string) (string, error) {
	name = strings.TrimSpace(name)
	if !eventLogAllowed(name) {
		return "", errors.New("event log is not authorized")
	}
	max := 100
	if v, err := strconv.Atoi(strings.TrimSpace(maxText)); err == nil && v >= 1 && v <= 200 {
		max = v
	}
	escaped := strings.ReplaceAll(name, "'", "''")
	ps := fmt.Sprintf(`Get-WinEvent -LogName '%s' -MaxEvents %d -ErrorAction Stop | Select-Object TimeCreated,Id,LevelDisplayName,ProviderName,RecordId | ConvertTo-Json -Compress`, escaped, max)
	return run(ctx, "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps)
}

func safeEnvironmentJSON() (string, error) {
	names := []string{"COMPUTERNAME", "USERDOMAIN", "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS", "OS", "ProgramData", "SystemDrive", "SystemRoot", "TEMP", "TMP"}
	out := map[string]string{}
	for _, name := range names {
		if v, ok := os.LookupEnv(name); ok {
			out[name] = v
		}
	}
	b, err := json.Marshal(out)
	if err != nil {
		return "", err
	}
	return string(b), nil
}

func fileACLJSON(ctx context.Context, cfg Config, path string) (string, error) {
	p, err := securePath(cfg, path)
	if err != nil {
		return "", err
	}
	escaped := strings.ReplaceAll(p, "'", "''")
	ps := `$a=Get-Acl -LiteralPath '` + escaped + `' -ErrorAction Stop; [pscustomobject]@{path='` + escaped + `';owner=$a.Owner;access=@($a.Access|Select-Object IdentityReference,FileSystemRights,AccessControlType,IsInherited,InheritanceFlags,PropagationFlags)}|ConvertTo-Json -Depth 5 -Compress`
	return run(ctx, "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps)
}
