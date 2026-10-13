package main

import (
    "crypto/subtle"
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "os"
    "path/filepath"
    "strings"
    "sync"
    "time"
)

type Job struct {
    ID             string            `json:"id"`
    Type           string            `json:"type"`
    Args           map[string]string `json:"args,omitempty"`
    TimeoutSeconds int               `json:"timeout_seconds"`
    CreatedAt      string            `json:"created_at"`
    Status         string            `json:"status"`
    Result         any               `json:"result,omitempty"`
}

type DeviceState struct {
    Heartbeat any             `json:"heartbeat,omitempty"`
    Queue     []string        `json:"queue,omitempty"`
    Jobs      map[string]*Job `json:"jobs,omitempty"`
}

type Store struct {
    sync.Mutex `json:"-"`
    Devices map[string]*DeviceState `json:"devices"`
}

var store = &Store{Devices: map[string]*DeviceState{}}
var deviceToken string
var controlToken string
var stateFile string

func main() {
    deviceToken = os.Getenv("DEVICE_TOKEN")
    controlToken = os.Getenv("CONTROL_TOKEN")
    if deviceToken == "" || controlToken == "" {
        log.Fatal("DEVICE_TOKEN and CONTROL_TOKEN are required")
    }
    stateFile = strings.TrimSpace(os.Getenv("ARA_STATE_FILE"))
    if stateFile != "" {
        if err := loadStore(stateFile); err != nil {
            log.Fatalf("load persistent state: %v", err)
        }
        log.Printf("persistent state enabled: %s", stateFile)
    }

    port := os.Getenv("PORT")
    if port == "" { port = "10000" }

    mux := http.NewServeMux()
    mux.HandleFunc("/health", health)
    mux.HandleFunc("/v1/device/heartbeat", deviceHeartbeat)
    mux.HandleFunc("/v1/device/jobs/next", deviceNext)
    mux.HandleFunc("/v1/device/jobs/", deviceResult)
    mux.HandleFunc("/v1/control/jobs", controlJobs)
    mux.HandleFunc("/v1/control/jobs/", controlJobByID)
    mux.HandleFunc("/v1/control/status", controlStatus)

    log.Printf("Anthares Remote Control listening on :%s", port)
    log.Fatal(http.ListenAndServe(":"+port, securityHeaders(mux)))
}

func loadStore(path string) error {
    if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil { return err }
    data, err := os.ReadFile(path)
    if os.IsNotExist(err) {
        return persistStore(path)
    }
    if err != nil { return err }
    if len(data) == 0 { return nil }
    var loaded Store
    if err := json.Unmarshal(data, &loaded); err != nil { return err }
    if loaded.Devices == nil { loaded.Devices = map[string]*DeviceState{} }
    for _, s := range loaded.Devices {
        if s.Jobs == nil { s.Jobs = map[string]*Job{} }
    }
    store = &loaded
    return nil
}

func persistStore(path string) error {
    if path == "" { return nil }
    if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil { return err }
    data, err := json.MarshalIndent(store, "", "  ")
    if err != nil { return err }
    tmp := path + ".tmp"
    if err := os.WriteFile(tmp, append(data, '\n'), 0600); err != nil { return err }
    return os.Rename(tmp, path)
}

func persistLocked() {
    if stateFile == "" { return }
    if err := persistStore(stateFile); err != nil {
        log.Printf("persist state failed: %v", err)
    }
}

func securityHeaders(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Cache-Control", "no-store")
        w.Header().Set("X-Content-Type-Options", "nosniff")
        next.ServeHTTP(w, r)
    })
}

func jsonWrite(w http.ResponseWriter, status int, v any) {
    w.Header().Set("Content-Type", "application/json; charset=utf-8")
    w.WriteHeader(status)
    _ = json.NewEncoder(w).Encode(v)
}

func health(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodGet { jsonWrite(w, 405, map[string]string{"error":"method_not_allowed"}); return }
    jsonWrite(w, 200, map[string]any{"ok":true,"service":"anthares-remote-control","version":"0.2.0","persistent":stateFile!=""})
}

func authBearer(r *http.Request, want string) bool {
    got := strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")
    if len(got) != len(want) || len(want) == 0 { return false }
    return subtle.ConstantTimeCompare([]byte(got), []byte(want)) == 1
}

func deviceID(r *http.Request) string { return strings.TrimSpace(r.Header.Get("X-Anthares-Device")) }

func requireDevice(w http.ResponseWriter, r *http.Request) (string, bool) {
    if !authBearer(r, deviceToken) { jsonWrite(w, 401, map[string]string{"error":"unauthorized"}); return "", false }
    id := deviceID(r)
    if id == "" { jsonWrite(w, 400, map[string]string{"error":"missing_device_id"}); return "", false }
    return id, true
}

func requireControl(w http.ResponseWriter, r *http.Request) bool {
    if !authBearer(r, controlToken) { jsonWrite(w, 401, map[string]string{"error":"unauthorized"}); return false }
    return true
}

func state(id string) *DeviceState {
    s := store.Devices[id]
    if s == nil { s = &DeviceState{Jobs: map[string]*Job{}}; store.Devices[id] = s }
    if s.Jobs == nil { s.Jobs = map[string]*Job{} }
    return s
}

func deviceHeartbeat(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost { jsonWrite(w,405,map[string]string{"error":"method_not_allowed"}); return }
    id, ok := requireDevice(w,r); if !ok { return }
    var body map[string]any
    if err := json.NewDecoder(http.MaxBytesReader(w,r.Body,1<<20)).Decode(&body); err != nil { jsonWrite(w,400,map[string]string{"error":"invalid_json"}); return }
    body["seen_at"] = time.Now().UTC().Format(time.RFC3339)
    store.Lock(); state(id).Heartbeat = body; persistLocked(); store.Unlock()
    jsonWrite(w,200,map[string]bool{"ok":true})
}

func deviceNext(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodGet { jsonWrite(w,405,map[string]string{"error":"method_not_allowed"}); return }
    id, ok := requireDevice(w,r); if !ok { return }
    store.Lock(); defer store.Unlock()
    s := state(id)
    for len(s.Queue) > 0 {
        jid := s.Queue[0]; s.Queue = s.Queue[1:]
        j := s.Jobs[jid]
        if j == nil || j.Status != "queued" { continue }
        j.Status = "leased"
        persistLocked()
        jsonWrite(w,200,map[string]any{"job":j}); return
    }
    persistLocked()
    w.WriteHeader(http.StatusNoContent)
}

func deviceResult(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost { jsonWrite(w,405,map[string]string{"error":"method_not_allowed"}); return }
    id, ok := requireDevice(w,r); if !ok { return }
    parts := strings.Split(strings.Trim(r.URL.Path,"/"), "/")
    if len(parts) != 5 || parts[0] != "v1" || parts[1] != "device" || parts[2] != "jobs" || parts[4] != "result" { jsonWrite(w,404,map[string]string{"error":"not_found"}); return }
    jid := parts[3]
    var body map[string]any
    if err := json.NewDecoder(http.MaxBytesReader(w,r.Body,2<<20)).Decode(&body); err != nil { jsonWrite(w,400,map[string]string{"error":"invalid_json"}); return }
    store.Lock(); defer store.Unlock()
    j := state(id).Jobs[jid]
    if j == nil { jsonWrite(w,404,map[string]string{"error":"unknown_job"}); return }
    j.Result = body
    if v, _ := body["ok"].(bool); v { j.Status = "done" } else { j.Status = "failed" }
    persistLocked()
    jsonWrite(w,200,map[string]bool{"ok":true})
}

func controlJobs(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost { jsonWrite(w,405,map[string]string{"error":"method_not_allowed"}); return }
    if !requireControl(w,r) { return }
    var body struct { DeviceID string `json:"device_id"`; Type string `json:"type"`; Args map[string]string `json:"args"`; Timeout int `json:"timeout_seconds"` }
    if err := json.NewDecoder(http.MaxBytesReader(w,r.Body,1<<20)).Decode(&body); err != nil { jsonWrite(w,400,map[string]string{"error":"invalid_json"}); return }
    body.DeviceID = strings.TrimSpace(body.DeviceID); body.Type = strings.TrimSpace(body.Type)
    if body.DeviceID == "" || body.Type == "" { jsonWrite(w,400,map[string]string{"error":"missing_device_id_or_type"}); return }
    if body.Timeout < 1 { body.Timeout = 30 }; if body.Timeout > 120 { body.Timeout = 120 }
    jid := fmt.Sprintf("%d-%d", time.Now().UnixNano(), len(body.Type))
    j := &Job{ID:jid,Type:body.Type,Args:body.Args,TimeoutSeconds:body.Timeout,CreatedAt:time.Now().UTC().Format(time.RFC3339),Status:"queued"}
    store.Lock(); s := state(body.DeviceID); s.Jobs[jid] = j; s.Queue = append(s.Queue,jid); persistLocked(); store.Unlock()
    jsonWrite(w,201,map[string]any{"ok":true,"job":j})
}

func controlJobByID(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodGet { jsonWrite(w,405,map[string]string{"error":"method_not_allowed"}); return }
    if !requireControl(w,r) { return }
    did := strings.TrimSpace(r.URL.Query().Get("device_id")); if did == "" { jsonWrite(w,400,map[string]string{"error":"missing_device_id"}); return }
    parts := strings.Split(strings.Trim(r.URL.Path,"/"), "/"); if len(parts) != 4 { jsonWrite(w,404,map[string]string{"error":"not_found"}); return }
    jid := parts[3]
    store.Lock(); j := state(did).Jobs[jid]; store.Unlock()
    if j == nil { jsonWrite(w,404,map[string]string{"error":"not_found"}); return }
    jsonWrite(w,200,map[string]any{"job":j})
}

func controlStatus(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodGet { jsonWrite(w,405,map[string]string{"error":"method_not_allowed"}); return }
    if !requireControl(w,r) { return }
    did := strings.TrimSpace(r.URL.Query().Get("device_id")); if did == "" { jsonWrite(w,400,map[string]string{"error":"missing_device_id"}); return }
    store.Lock(); s := state(did); hb := s.Heartbeat; q := len(s.Queue); store.Unlock()
    jsonWrite(w,200,map[string]any{"heartbeat":hb,"queued":q})
}
