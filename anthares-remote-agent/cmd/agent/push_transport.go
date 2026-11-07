package main

import (
    "fmt"
    "net/http"
    "os"
    "path/filepath"
    "strings"
    "sync/atomic"
    "time"

    "github.com/gorilla/websocket"
)

const araPushURL = "wss://anthares-ara-mcp.anthares1.workers.dev/_ara_live/device"

// runPushTransport keeps one authenticated WebSocket open while idle.
// The existing GitHub/GitLab issue queues continue in their own goroutines;
// Cloudflare is contacted for jobs only after receiving a wake event.
func runPushTransport(cfg Config) {
    var draining atomic.Bool
    slots := executionSemaphore(cfg.MaxConcurrent)
    backoff := 2 * time.Second
    for {
        headers := http.Header{}
        headers.Set("Authorization", "Bearer "+cfg.DeviceToken)
        headers.Set("X-Anthares-Device", cfg.DeviceID)
        headers.Set("User-Agent", "AntharesRemoteAgent/0.4.0 CF06-Push")
        conn, response, err := websocket.DefaultDialer.Dial(araPushURL, headers)
        if err != nil {
            code := 0
            if response != nil { code = response.StatusCode; _ = response.Body.Close() }
            // Never print a bearer token, request headers or response body.
            fmt.Fprintf(os.Stderr, "ARA push connection deferred status=%d error=%T\n", code, err)
            time.Sleep(backoff)
            if backoff < 60*time.Second { backoff *= 2 }
            if backoff > 60*time.Second { backoff = 60*time.Second }
            continue
        }
        backoff = 2 * time.Second
        fmt.Println("ARA_PUSH_CONNECTED=1 transport=websocket-hibernation")
        finished := make(chan struct{})
        go func() {
            ticker := time.NewTicker(55 * time.Second)
            defer ticker.Stop()
            defer close(finished)
            for range ticker.C {
                if err := conn.WriteControl(websocket.PingMessage, []byte("cf06"), time.Now().Add(6*time.Second)); err != nil { return }
            }
        }()
        for {
            messageType, payload, err := conn.ReadMessage()
            if err != nil {
                fmt.Fprintf(os.Stderr, "ARA push socket disconnected error=%T\n", err)
                break
            }
            if messageType != websocket.TextMessage || strings.TrimSpace(string(payload)) != "wake" { continue }
            if draining.CompareAndSwap(false, true) {
                go func() {
                    defer draining.Store(false)
                    drainJobsOnWake(cfg, slots)
                }()
            }
        }
        _ = conn.Close()
        // Reconnect after the existing authenticated session ends; the DO
        // always sends a wake on a fresh connection to recover queued jobs.
        time.Sleep(time.Second)
    }
}

func drainJobsOnWake(cfg Config, slots chan struct{}) {
    empty := 0
    for empty < 24 {
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
            time.Sleep(200 * time.Millisecond)
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
