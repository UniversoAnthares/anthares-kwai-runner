package main

import (
    "fmt"
    "net/http"
    "os"
    "path/filepath"
    "strings"
    "math/rand"
    "time"

    "github.com/gorilla/websocket"
)

const araPushURL = "wss://anthares-ara-mcp.anthares1.workers.dev/_ara_live/device"

// runPushTransport keeps one authenticated WebSocket open while idle.
// The existing GitHub/GitLab issue queues continue in their own goroutines;
// Cloudflare is contacted for jobs only after receiving a wake event.
func runPushTransport(cfg Config) {
    slots := executionSemaphore(cfg.MaxConcurrent)
    backoff := 2 * time.Second
    for {
        headers := http.Header{}
        headers.Set("Authorization", "Bearer "+cfg.DeviceToken)
        headers.Set("X-Anthares-Device", cfg.DeviceID)
        headers.Set("User-Agent", "AntharesRemoteAgent/0.4.0 CF07-Push")
        conn, response, err := websocket.DefaultDialer.Dial(araPushURL, headers)
        if err != nil {
            code := 0
            if response != nil { code = response.StatusCode; _ = response.Body.Close() }
            // Never expose device credentials, request headers or response bodies.
            fmt.Fprintf(os.Stderr, "ARA push connection deferred status=%d error=%T\n", code, err)
            time.Sleep(backoff + time.Duration(rand.Int63n(int64(backoff/5)+1)))
            if backoff < 60*time.Second { backoff *= 2 }
            if backoff > 60*time.Second { backoff = 60*time.Second }
            continue
        }
        connectedSince := time.Now()
        fmt.Println("ARA_PUSH_CONNECTED=1 transport=websocket-hibernation")
        // WebSocket protocol Ping frames are not billed as Worker requests and
        // keep idle connections alive without waking the hibernating DO.
        stopPing := make(chan struct{})
        go func() {
            ticker := time.NewTicker(55 * time.Second)
            defer ticker.Stop()
            for {
                select {
                case <-stopPing: return
                case <-ticker.C:
                    if err := conn.WriteControl(websocket.PingMessage, []byte("cf07"), time.Now().Add(6*time.Second)); err != nil { return }
                }
            }
        }()
        // A one-place buffer coalesces simultaneous wake notifications while
        // preserving one pending wake after an already running drain.
        wakeQueue := make(chan struct{}, 1)
        stopWorker := make(chan struct{})
        go func() {
            for {
                select {
                case <-stopWorker: return
                case <-wakeQueue: drainJobsOnWake(cfg, slots)
                }
            }
        }()
        for {
            messageType, payload, err := conn.ReadMessage()
            if err != nil {
                fmt.Fprintf(os.Stderr, "ARA push socket disconnected error=%T\n", err)
                break
            }
            if messageType != websocket.TextMessage || strings.TrimSpace(string(payload)) != "wake" { continue }
            select {case wakeQueue <- struct{}{}: default:}
        }
        close(stopPing)
        close(stopWorker)
        _ = conn.Close()
        // An unstable connection must not generate rapid repeat handshakes.
        // Stable sessions return to the shortest recovery interval.
        if time.Since(connectedSince) >= 30*time.Second {backoff = 2*time.Second}
        time.Sleep(backoff + time.Duration(rand.Int63n(int64(backoff/5)+1)))
        if backoff < 60*time.Second {backoff *= 2}
        if backoff > 60*time.Second {backoff = 60*time.Second}
    }
}

func drainJobsOnWake(cfg Config, slots chan struct{}) {
    empty := 0
    for empty < 4 {
        slots <- struct{}{}
        job, err := pollJob(cfg)
        if err != nil {
            <-slots
            fmt.Fprintf(os.Stderr, "ARA push job fetch deferred error=%T\n", err)
            return
        }
        if job == nil {
            <-slots
            empty++
            if empty >= 4 {return}
            time.Sleep(time.Duration(1<<(empty-1)) * 150 * time.Millisecond)
            continue
        }
        if err := validateJobID(job.ID); err != nil || strings.TrimSpace(job.Type) == "" {
            <-slots
            fmt.Fprintln(os.Stderr, "ARA push rejected malformed job")
            continue
        }
        empty = 0
        j := *job
        go func() {
            defer func(){ <-slots }()
            result := executeJob(cfg, j)
            if err := saveEncryptedResult(resultSpoolDir(cfg), cfg.DeviceToken, result); err != nil {
                fmt.Fprintf(os.Stderr, "fatal result spool error job=%s: %v\n", result.ID, err)
                os.Exit(1)
            }
            if err := postResultRetry(cfg, result); err != nil {
                fmt.Fprintf(os.Stderr, "ARA push result upload deferred job=%s: %v\n", result.ID, err)
                return
            }
            if err := os.Remove(filepath.Join(resultSpoolDir(cfg), result.ID+".pending")); err != nil {
                fmt.Fprintf(os.Stderr, "ARA push result cleanup deferred job=%s: %v\n", result.ID, err)
            }
        }()
    }
}
