package main

import (
    "bytes"
    "context"
    "encoding/base64"
    "encoding/json"
    "errors"
    "fmt"
    "io"
    "net/http"
    "net/url"
    "os"
    "os/exec"
    "path/filepath"
    "runtime"
    "strconv"
    "strings"
    "time"
)

type Config struct {
    ControlURL    string
    DeviceToken  string
    DeviceID     string
    AllowShell   bool
    AllowedRoots []string
    MaxConcurrent int
}

type Job struct {
    ID             string            `json:"id"`
    Type           string            `json:"type"`
    Args           map[string]string `json:"args"`
    TimeoutSeconds int               `json:"timeout_seconds"`
}

type JobEnvelope struct { Job *Job `json:"job"` }

type Result struct {
    ID        string `json:"id"`
    OK        bool   `json:"ok"`
    Output    string `json:"output,omitempty"`
    Error     string `json:"error,omitempty"`
    StartedAt string `json:"started_at"`
    EndedAt   string `json:"ended_at"`
}

var httpClient = &http.Client{Timeout: 35 * time.Second}

func main() {
    cfg, err := loadConfig()
    if err != nil { fmt.Fprintln(os.Stderr, "config error:", err); os.Exit(2) }
    fmt.Printf("Anthares Remote Agent starting device=%s os=%s/%s concurrency=%d\n", cfg.DeviceID, runtime.GOOS, runtime.GOARCH, cfg.MaxConcurrent)
    go heartbeatLoop(cfg)

    sem := make(chan struct{}, cfg.MaxConcurrent)
    for {
        job, err := pollJob(cfg)
        if err != nil { fmt.Fprintln(os.Stderr, "poll error:", err); time.Sleep(3 * time.Second); continue }
        if job == nil { time.Sleep(2 * time.Second); continue }
        sem <- struct{}{}
        j := *job
        go func() {
            defer func(){ <-sem }()
            result := executeJob(cfg, j)
            if err := postResultRetry(cfg, result); err != nil {
                fmt.Fprintf(os.Stderr, "result upload error job=%s: %v\n", result.ID, err)
            }
        }()
    }
}

func loadConfig() (Config, error) {
    c := Config{
        ControlURL: strings.TrimRight(os.Getenv("ANTHARES_CONTROL_URL"), "/"),
        DeviceToken: os.Getenv("ANTHARES_DEVICE_TOKEN"),
        DeviceID: os.Getenv("ANTHARES_DEVICE_ID"),
        AllowShell: os.Getenv("ANTHARES_ALLOW_SHELL") == "1",
        MaxConcurrent: 4,
    }
    if v, err := strconv.Atoi(os.Getenv("ANTHARES_MAX_CONCURRENT")); err == nil && v >= 1 && v <= 8 { c.MaxConcurrent = v }
    if roots := os.Getenv("ANTHARES_ALLOWED_ROOTS"); roots != "" {
        for _, root := range strings.Split(roots, ";") {
            root = strings.TrimSpace(root)
            if root != "" {
                if abs, err := filepath.Abs(root); err == nil { c.AllowedRoots = append(c.AllowedRoots, filepath.Clean(abs)) }
            }
        }
    }
    if c.ControlURL == "" || c.DeviceToken == "" || c.DeviceID == "" {
        return c, errors.New("ANTHARES_CONTROL_URL, ANTHARES_DEVICE_TOKEN and ANTHARES_DEVICE_ID are required")
    }
    u, err := url.Parse(c.ControlURL)
    if err != nil || u.Scheme != "https" || u.Hostname() == "" || u.User != nil || u.RawQuery != "" || u.Fragment != "" || (u.Path != "" && u.Path != "/") {
        return c, errors.New("ANTHARES_CONTROL_URL must be an HTTPS origin without credentials, path, query or fragment")
    }
    return c, nil
}

func authReq(req *http.Request, cfg Config) {
    req.Header.Set("Authorization", "Bearer "+cfg.DeviceToken)
    req.Header.Set("X-Anthares-Device", cfg.DeviceID)
    req.Header.Set("User-Agent", "AntharesRemoteAgent/0.3")
}

func heartbeatLoop(cfg Config) {
    ticker := time.NewTicker(15*time.Second); defer ticker.Stop()
    for { _ = heartbeat(cfg); <-ticker.C }
}

func heartbeat(cfg Config) error {
    body, _ := json.Marshal(map[string]any{"device_id":cfg.DeviceID,"hostname":hostname(),"os":runtime.GOOS,"arch":runtime.GOARCH,"version":"0.3.0","time":time.Now().UTC().Format(time.RFC3339)})
    req, _ := http.NewRequest(http.MethodPost, cfg.ControlURL+"/v1/device/heartbeat", bytes.NewReader(body))
    req.Header.Set("Content-Type", "application/json"); authReq(req,cfg)
    resp, err := httpClient.Do(req); if err != nil { return err }; defer resp.Body.Close()
    if resp.StatusCode/100 != 2 { return fmt.Errorf("heartbeat status %d", resp.StatusCode) }
    return nil
}

func pollJob(cfg Config) (*Job, error) {
    req,_:=http.NewRequest(http.MethodGet,cfg.ControlURL+"/v1/device/jobs/next",nil); authReq(req,cfg)
    resp,err:=httpClient.Do(req); if err!=nil{return nil,err}; defer resp.Body.Close()
    if resp.StatusCode==http.StatusNoContent{return nil,nil}
    if resp.StatusCode/100!=2{return nil,fmt.Errorf("poll status %d",resp.StatusCode)}
    var env JobEnvelope
    if err:=json.NewDecoder(io.LimitReader(resp.Body,1<<20)).Decode(&env);err!=nil{return nil,err}
    return env.Job,nil
}

func executeJob(cfg Config, job Job) Result {
    start:=time.Now().UTC(); timeout:=job.TimeoutSeconds
    if timeout<=0||timeout>120{timeout=30}
    ctx,cancel:=context.WithTimeout(context.Background(),time.Duration(timeout)*time.Second); defer cancel()
    out,err:=dispatch(ctx,cfg,job)
    r:=Result{ID:job.ID,OK:err==nil,StartedAt:start.Format(time.RFC3339),EndedAt:time.Now().UTC().Format(time.RFC3339)}
    r.Output=out
    if err!=nil{r.Error=err.Error()}
    return r
}

func boolArg(v string) bool { return v=="1" || strings.EqualFold(v,"true") || strings.EqualFold(v,"yes") }

func dispatch(ctx context.Context, cfg Config, job Job) (string,error) {
    switch job.Type {
    case "ping": return "pong",nil
    case "system_info": return systemInfoJSON(ctx)
    case "safe_environment": return safeEnvironmentJSON()
    case "network_info": return networkInfoJSON(ctx)
    case "tcp_connections": return tcpConnectionsJSON(ctx)
    case "scheduled_tasks": return scheduledTasksJSON(ctx)
    case "event_log": return eventLogJSON(ctx,job.Args["name"],job.Args["max"])
    case "process_list": return run(ctx,"tasklist","/FO","CSV")
    case "process_info": return processInfoJSON(ctx,job.Args["pid"])
    case "process_start": return processStartJSON(job.Args["path"], job.Args["args_json"])
    case "process_kill": return processKillJSON(job.Args["pid"])
    case "service_list": return serviceListJSON(ctx)
    case "service_status": return serviceStatusJSON(ctx,job.Args["name"])
    case "service_start": return serviceControlJSON(ctx,job.Args["name"],true)
    case "service_stop": return serviceControlJSON(ctx,job.Args["name"],false)
    case "clipboard_get": return run(ctx,"powershell.exe","-NoProfile","-NonInteractive","-Command","Get-Clipboard -Raw")
    case "clipboard_set": return runWithStdin(ctx,job.Args["text"],"powershell.exe","-NoProfile","-NonInteractive","-Command","$input | Set-Clipboard")
    case "screenshot": return screenshotBase64(ctx,job.Args["display"])
    case "file_acl": return fileACLJSON(ctx,cfg,job.Args["path"])
    case "file_stat": return fileStatJSON(cfg,job.Args["path"])
    case "file_list": return fileListJSON(cfg,job.Args["path"])
    case "file_mkdir": return fileMkdir(cfg,job.Args["path"])
    case "file_remove": return fileRemove(cfg,job.Args["path"],boolArg(job.Args["recursive"]))
    case "file_rename": return fileRename(cfg,job.Args["src"],job.Args["dst"])
    case "file_copy": return fileCopy(cfg,job.Args["src"],job.Args["dst"])
    case "file_sha256": return fileSHA256(cfg,job.Args["path"])
    case "file_write_atomic":
        b,err:=base64.StdEncoding.DecodeString(job.Args["base64"]); if err!=nil{return "",err}; return fileWriteAtomic(cfg,job.Args["path"],b)
    case "file_read_chunk":
        off,err:=strconv.ParseInt(job.Args["offset"],10,64); if err!=nil{return "",errors.New("invalid offset")}
        ln,err:=strconv.ParseInt(job.Args["length"],10,64); if err!=nil{return "",errors.New("invalid length")}
        return fileReadChunk(cfg,job.Args["path"],off,ln)
    case "file_write_chunk":
        off,err:=strconv.ParseInt(job.Args["offset"],10,64); if err!=nil{return "",errors.New("invalid offset")}
        return fileWriteChunk(cfg,job.Args["path"],off,job.Args["base64"],boolArg(job.Args["truncate"]))
    case "file_read":
        p,err:=securePath(cfg,job.Args["path"]); if err!=nil{return "",err}
        b,err:=os.ReadFile(p); if err!=nil{return "",err}; if len(b)>1<<20{return "",errors.New("file exceeds 1 MiB limit")}
        return base64.StdEncoding.EncodeToString(b),nil
    case "file_write":
        p,err:=securePath(cfg,job.Args["path"]); if err!=nil{return "",err}
        b,err:=base64.StdEncoding.DecodeString(job.Args["base64"]); if err!=nil{return "",err}; if len(b)>1<<20{return "",errors.New("file exceeds 1 MiB limit")}
        return fileWriteAtomic(cfg,p,b)
    case "job_start":
        if !cfg.AllowShell{return "",errors.New("shell disabled")}; return startDetachedJob(job.Args["command"],job.Args["name"])
    case "job_list":
        limit,_:=strconv.Atoi(job.Args["limit"]); return jobListJSON(boolArg(job.Args["include_command"]),limit)
    case "job_status": return jobStatusJSON(job.Args["job_id"],boolArg(job.Args["include_command"]))
    case "job_logs":
        off:=int64(-1); if v:=job.Args["offset_bytes"];v!=""{off,_=strconv.ParseInt(v,10,64)}
        max,_:=strconv.Atoi(job.Args["max_bytes"]); tail,_:=strconv.Atoi(job.Args["tail_lines"])
        return jobLogsJSON(job.Args["job_id"],off,max,tail)
    case "job_cancel": return jobCancelJSON(job.Args["job_id"])
    case "shell":
        if !cfg.AllowShell{return "",errors.New("shell disabled; set ANTHARES_ALLOW_SHELL=1 to enable")}
        cmd:=strings.TrimSpace(job.Args["command"]); if cmd==""{return "",errors.New("missing command")}
        shell:=strings.ToLower(strings.TrimSpace(job.Args["shell"]))
        return shellExecJSON(ctx,shell,cmd)
    default: return "",fmt.Errorf("unsupported job type %q",job.Type)
    }
}

func safePath(cfg Config,p string)(string,error){ return securePath(cfg,p) }

func run(ctx context.Context,name string,args ...string)(string,error){
    cmd:=exec.CommandContext(ctx,name,args...); var out bytes.Buffer; cmd.Stdout=&out; cmd.Stderr=&out
    err:=cmd.Run(); s:=out.String(); if len(s)>1<<20{s=s[:1<<20]+"\n[truncated]"}
    if ctx.Err()==context.DeadlineExceeded{return s,errors.New("command timed out")}
    return s,err
}

func runWithStdin(ctx context.Context,stdin,name string,args ...string)(string,error){
    cmd:=exec.CommandContext(ctx,name,args...); cmd.Stdin=strings.NewReader(stdin); var out bytes.Buffer; cmd.Stdout=&out; cmd.Stderr=&out
    err:=cmd.Run(); if ctx.Err()==context.DeadlineExceeded{return out.String(),errors.New("command timed out")}; return out.String(),err
}

func postResult(cfg Config,result Result)error{
    if err:=validateJobID(result.ID);err!=nil{return err}
    body,_:=json.Marshal(result)
    req,err:=http.NewRequest(http.MethodPost,cfg.ControlURL+"/v1/device/jobs/"+url.PathEscape(result.ID)+"/result",bytes.NewReader(body))
    if err!=nil{return err}
    req.Header.Set("Content-Type","application/json"); authReq(req,cfg)
    resp,err:=httpClient.Do(req);if err!=nil{return err};defer resp.Body.Close()
    if resp.StatusCode/100!=2{return fmt.Errorf("result status %d",resp.StatusCode)}
    return nil
}

func postResultRetry(cfg Config, result Result) error {
    var last error
    for attempt:=0; attempt<5; attempt++ {
        if err:=postResult(cfg,result); err==nil { return nil } else { last=err }
        time.Sleep(time.Duration(1<<attempt)*time.Second)
    }
    return last
}

func hostname()string{h,_:=os.Hostname();return h}

// validateJobID prevents job IDs from escaping the control-plane result route.
func validateJobID(id string) error {
    if len(id)==0 || len(id)>128 {return errors.New("invalid job ID length")}
    for _,ch:=range id {
        if !(ch>='a'&&ch<='z' || ch>='A'&&ch<='Z' || ch>='0'&&ch<='9' || ch=='-' || ch=='_') {
            return errors.New("invalid job ID character")
        }
    }
    return nil
}
