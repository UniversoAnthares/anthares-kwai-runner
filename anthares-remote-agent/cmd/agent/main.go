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
    fmt.Printf("Anthares Remote Agent starting device=%s os=%s/%s\n", cfg.DeviceID, runtime.GOOS, runtime.GOARCH)
    go heartbeatLoop(cfg)
    for {
        job, err := pollJob(cfg)
        if err != nil { fmt.Fprintln(os.Stderr, "poll error:", err); time.Sleep(3 * time.Second); continue }
        if job == nil { time.Sleep(2 * time.Second); continue }
        result := executeJob(cfg, *job)
        if err := postResult(cfg, result); err != nil { fmt.Fprintln(os.Stderr, "result upload error:", err) }
    }
}

func loadConfig() (Config, error) {
    c := Config{
        ControlURL: strings.TrimRight(os.Getenv("ANTHARES_CONTROL_URL"), "/"),
        DeviceToken: os.Getenv("ANTHARES_DEVICE_TOKEN"), DeviceID: os.Getenv("ANTHARES_DEVICE_ID"),
        AllowShell: os.Getenv("ANTHARES_ALLOW_SHELL") == "1",
    }
    if roots := os.Getenv("ANTHARES_ALLOWED_ROOTS"); roots != "" {
        for _, root := range strings.Split(roots, ";") {
            root = strings.TrimSpace(root)
            if root != "" { if abs, err := filepath.Abs(root); err == nil { c.AllowedRoots = append(c.AllowedRoots, filepath.Clean(abs)) } }
        }
    }
    if !strings.HasPrefix(c.ControlURL, "https://") { return c, errors.New("ANTHARES_CONTROL_URL must use HTTPS") }; if c.ControlURL == "" || c.DeviceToken == "" || c.DeviceID == "" { return c, errors.New("ANTHARES_CONTROL_URL, ANTHARES_DEVICE_TOKEN and ANTHARES_DEVICE_ID are required") }
    return c, nil
}

func authReq(req *http.Request, cfg Config) {
    req.Header.Set("Authorization", "Bearer "+cfg.DeviceToken)
    req.Header.Set("X-Anthares-Device", cfg.DeviceID)
    req.Header.Set("User-Agent", "AntharesRemoteAgent/0.2")
}

func heartbeatLoop(cfg Config) { ticker := time.NewTicker(15*time.Second); defer ticker.Stop(); for { _ = heartbeat(cfg); <-ticker.C } }

func heartbeat(cfg Config) error {
    body, _ := json.Marshal(map[string]any{"device_id":cfg.DeviceID,"hostname":hostname(),"os":runtime.GOOS,"arch":runtime.GOARCH,"version":"0.2.0","time":time.Now().UTC().Format(time.RFC3339)})
    req, _ := http.NewRequest(http.MethodPost, cfg.ControlURL+"/v1/device/heartbeat", bytes.NewReader(body)); req.Header.Set("Content-Type", "application/json"); authReq(req,cfg)
    resp, err := httpClient.Do(req); if err != nil { return err }; defer resp.Body.Close(); if resp.StatusCode/100 != 2 { return fmt.Errorf("heartbeat status %d", resp.StatusCode) }; return nil
}

func pollJob(cfg Config) (*Job, error) {
    req,_:=http.NewRequest(http.MethodGet,cfg.ControlURL+"/v1/device/jobs/next",nil); authReq(req,cfg)
    resp,err:=httpClient.Do(req); if err!=nil{return nil,err}; defer resp.Body.Close(); if resp.StatusCode==http.StatusNoContent{return nil,nil}; if resp.StatusCode/100!=2{return nil,fmt.Errorf("poll status %d",resp.StatusCode)}
    var env JobEnvelope; if err:=json.NewDecoder(io.LimitReader(resp.Body,1<<20)).Decode(&env);err!=nil{return nil,err}; return env.Job,nil
}

func executeJob(cfg Config, job Job) Result {
    start:=time.Now().UTC(); timeout:=job.TimeoutSeconds; if timeout<=0||timeout>120{timeout=30}; ctx,cancel:=context.WithTimeout(context.Background(),time.Duration(timeout)*time.Second); defer cancel()
    out,err:=dispatch(ctx,cfg,job); r:=Result{ID:job.ID,OK:err==nil,StartedAt:start.Format(time.RFC3339),EndedAt:time.Now().UTC().Format(time.RFC3339)}; if err!=nil{r.Error=err.Error()}else{r.Output=out}; return r
}

func dispatch(ctx context.Context, cfg Config, job Job) (string,error) {
    switch job.Type {
    case "ping": return "pong",nil
    case "system_info":
        out,_:=run(ctx,"powershell.exe","-NoProfile","-NonInteractive","-Command","$ErrorActionPreference='SilentlyContinue'; $os=Get-CimInstance Win32_OperatingSystem; $cpu=Get-CimInstance Win32_Processor | Select-Object -First 1; $gpu=Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion; [pscustomobject]@{hostname=$env:COMPUTERNAME;user=[Environment]::UserName;os=$os.Caption;version=$os.Version;arch=$env:PROCESSOR_ARCHITECTURE;cpu=$cpu.Name;ram_bytes=[int64]$os.TotalVisibleMemorySize*1024;gpu=$gpu}|ConvertTo-Json -Depth 4 -Compress"); if strings.TrimSpace(out)!=""{return out,nil}; return fmt.Sprintf("hostname=%s os=%s arch=%s",hostname(),runtime.GOOS,runtime.GOARCH),nil
    case "process_list": return run(ctx,"tasklist","/FO","CSV")
    case "clipboard_get": return run(ctx,"powershell.exe","-NoProfile","-NonInteractive","-Command","Get-Clipboard -Raw")
    case "clipboard_set": return runWithStdin(ctx,job.Args["text"],"powershell.exe","-NoProfile","-NonInteractive","-Command","$input | Set-Clipboard")
    case "screenshot": return screenshotBase64(ctx,job.Args["display"])
    case "file_stat": return fileStatJSON(cfg,job.Args["path"])
    case "file_list": return fileListJSON(cfg,job.Args["path"])
    case "file_read_chunk":
        off,_:=strconv.ParseInt(job.Args["offset"],10,64); ln,_:=strconv.ParseInt(job.Args["length"],10,64); return fileReadChunk(cfg,job.Args["path"],off,ln)
    case "file_write_chunk":
        off,_:=strconv.ParseInt(job.Args["offset"],10,64); trunc:=strings.EqualFold(job.Args["truncate"],"true")||job.Args["truncate"]=="1"; return fileWriteChunk(cfg,job.Args["path"],off,job.Args["base64"],trunc)
    case "file_read":
        p,err:=safeExistingPath(cfg,job.Args["path"]); if err!=nil{return "",err}; b,err:=os.ReadFile(p); if err!=nil{return "",err}; if len(b)>1<<20{return "",errors.New("file exceeds 1 MiB limit")}; return base64.StdEncoding.EncodeToString(b),nil
    case "file_write":
        p,err:=safeExistingPath(cfg,job.Args["path"]); if err!=nil{return "",err}; b,err:=base64.StdEncoding.DecodeString(job.Args["base64"]); if err!=nil{return "",err}; if len(b)>1<<20{return "",errors.New("file exceeds 1 MiB limit")}; if err:=os.MkdirAll(filepath.Dir(p),0700);err!=nil{return "",err}; if err:=os.WriteFile(p,b,0600);err!=nil{return "",err}; return fmt.Sprintf("wrote %d bytes",len(b)),nil
    case "job_start":
        if !cfg.AllowShell{return "",errors.New("shell disabled")}; return startDetachedJob(job.Args["command"],job.Args["name"])
    case "job_list":
        limit,_:=strconv.Atoi(job.Args["limit"]); include:=job.Args["include_command"]=="1"||strings.EqualFold(job.Args["include_command"],"true"); return jobListJSON(include,limit)
    case "job_status":
        include:=job.Args["include_command"]=="1"||strings.EqualFold(job.Args["include_command"],"true"); return jobStatusJSON(job.Args["job_id"],include)
    case "job_logs":
        off:=int64(-1); if v:=job.Args["offset_bytes"];v!=""{off,_=strconv.ParseInt(v,10,64)}; max,_:=strconv.Atoi(job.Args["max_bytes"]); tail,_:=strconv.Atoi(job.Args["tail_lines"]); return jobLogsJSON(job.Args["job_id"],off,max,tail)
    case "job_cancel": return jobCancelJSON(job.Args["job_id"])
    case "shell":
        if !cfg.AllowShell{return "",errors.New("shell disabled; set ANTHARES_ALLOW_SHELL=1 to enable")}; cmd:=strings.TrimSpace(job.Args["command"]); if cmd==""{return "",errors.New("missing command")}
        shell:=strings.ToLower(strings.TrimSpace(job.Args["shell"])); switch shell {case "cmd": return run(ctx,"cmd.exe","/d","/s","/c",cmd); case "powershell", "": return run(ctx,"powershell.exe","-NoProfile","-NonInteractive","-Command",cmd); default:return "",fmt.Errorf("unsupported shell %q",shell)}
    default: return "",fmt.Errorf("unsupported job type %q",job.Type)
    }
}

func safePath(cfg Config,p string)(string,error){if len(cfg.AllowedRoots)==0{return "",errors.New("file access disabled; ANTHARES_ALLOWED_ROOTS is empty")}; abs,err:=filepath.Abs(p);if err!=nil{return "",err};abs=filepath.Clean(abs);lower:=strings.ToLower(abs);for _,root:=range cfg.AllowedRoots{r:=strings.ToLower(filepath.Clean(root));if lower==r||strings.HasPrefix(lower,r+string(os.PathSeparator)){return abs,nil}};return "",errors.New("path outside allowed roots")}

func run(ctx context.Context,name string,args ...string)(string,error){cmd:=exec.CommandContext(ctx,name,args...);var out bytes.Buffer;cmd.Stdout=&out;cmd.Stderr=&out;err:=cmd.Run();s:=out.String();if len(s)>1<<20{s=s[:1<<20]+"\n[truncated]"};if ctx.Err()==context.DeadlineExceeded{return s,errors.New("command timed out")};return s,err}

func runWithStdin(ctx context.Context,stdin,name string,args ...string)(string,error){cmd:=exec.CommandContext(ctx,name,args...);cmd.Stdin=strings.NewReader(stdin);var out bytes.Buffer;cmd.Stdout=&out;cmd.Stderr=&out;err:=cmd.Run();return out.String(),err}

func postResult(cfg Config,result Result)error{body,_:=json.Marshal(result);req,_:=http.NewRequest(http.MethodPost,cfg.ControlURL+"/v1/device/jobs/"+result.ID+"/result",bytes.NewReader(body));req.Header.Set("Content-Type","application/json");authReq(req,cfg);resp,err:=httpClient.Do(req);if err!=nil{return err};defer resp.Body.Close();if resp.StatusCode/100!=2{return fmt.Errorf("result status %d",resp.StatusCode)};return nil}

func hostname()string{h,_:=os.Hostname();return h}
