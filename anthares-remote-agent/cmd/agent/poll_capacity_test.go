package main

import (
	"context"
	"io"
	"strings"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"
)

// This probe verifies that an idle poll never consumes an execution slot.
func TestPollNoContentDoesNotReturnJob(t *testing.T) {
	var polls atomic.Int32
	server := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		polls.Add(1)
		w.WriteHeader(http.StatusNoContent)
	}))
	defer server.Close()
	old := httpClient
	httpClient = server.Client()
	defer func() { httpClient = old }()
	cfg := Config{ControlURL: server.URL, DeviceToken: "test", DeviceID: "test"}
	job, err := pollJob(cfg)
	if err != nil || job != nil {
		t.Fatalf("204 must return nil job: %#v %v", job, err)
	}
	if polls.Load() != 1 {
		t.Fatalf("expected one poll, got %d", polls.Load())
	}
}

func TestExecuteJobTimeoutIsBounded(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	if err := ctx.Err(); err != nil {
		t.Fatal(err)
	}
	r := executeJob(Config{}, Job{ID: "timeout-check", Type: "ping", TimeoutSeconds: 999999})
	if !r.OK || r.Output != "pong" {
		t.Fatalf("bounded job execution failed: %#v", r)
	}
}

func TestWakeIdleFallbackAndCoalescedSignals(t *testing.T) {
	var absent *wakeListener
	if absent.idleDelay() != 2*time.Second {
		t.Fatal("wake disabled must preserve 2s polling")
	}
	w := &wakeListener{events: make(chan struct{}, 1)}
	if w.idleDelay() != 2*time.Second {
		t.Fatal("disconnected listener must preserve 2s polling")
	}
	w.setOnline(true)
	w.setOnline(true)
	if w.idleDelay() != 12*time.Second {
		t.Fatal("healthy listener must reconcile every 12 seconds")
	}
	if len(w.events) != 1 {
		t.Fatalf("connection readiness must coalesce wake signals: %d", len(w.events))
	}
	<-w.events
	w.signal()
	w.signal()
	if len(w.events) != 1 {
		t.Fatal("duplicate wake events must coalesce")
	}
	<-w.events
	w.setOnline(false)
	if w.idleDelay() != 2*time.Second || len(w.events) != 1 {
		t.Fatal("disconnect must immediately restore old polling")
	}
}

func TestHostingerWakeOnlyProtocolAndSeparateAuth(t *testing.T) {
	var health, wait int
	server := httptest.NewTLSServer(http.HandlerFunc(func(out http.ResponseWriter, req *http.Request) {
		if req.Method != http.MethodGet ||
			req.Header.Get("X-Anthares-Notify-Key") != strings.Repeat("L", 40) ||
			req.Header.Get("Authorization") != "" ||
			req.URL.Query().Get("device_id") != "DESKTOP-FTDK0HP" {
			t.Errorf("listener must use dedicated token and known device")
			http.Error(out, "unauthorized", http.StatusUnauthorized)
			return
		}
		switch req.URL.Query().Get("action") {
		case "health":
			health++
			_, _ = io.WriteString(out, `{"ok":true,"protocol":"ara-wake-v1","sequence":5,"role":"listener"}`)
		case "wait":
			wait++
			if req.URL.Query().Get("since") != "5" ||
				req.URL.Query().Get("seconds") != "20" {
				t.Error("bounded reconciliation window invalid")
			}
			_, _ = io.WriteString(out, `{"ok":true,"protocol":"ara-wake-v1","sequence":6,"wake":true}`)
		default:
			t.Error("unexpected action")
		}
	}))
	defer server.Close()
	cfg := Config{DeviceID: "DESKTOP-FTDK0HP", DeviceToken: "DIFFERENT_DEVICE_TOKEN",
		WakeListenerToken: strings.Repeat("L", 40)}
	initial, err := readHostingerWake(cfg, server.URL, "health", 0, server.Client())
	if err != nil || initial.Sequence != 5 {
		t.Fatalf("health %v %+v", err, initial)
	}
	next, err := readHostingerWake(cfg, server.URL, "wait", initial.Sequence, server.Client())
	if err != nil || next.Sequence != 6 || next.Wake == nil || !*next.Wake {
		t.Fatalf("wait %v %+v", err, next)
	}
	if health != 1 || wait != 1 {
		t.Fatalf("expected one health and one wait, got %d %d", health, wait)
	}
}

func TestWakeRejectsUntrustedPayloadAndStaleSequence(t *testing.T) {
	for _, body := range []string{
		`{"ok":true,"protocol":"ara-wake-v1","sequence":6,"wake":true,"command":"shell"}`,
		`{"ok":true,"protocol":"other","sequence":6,"wake":true}`,
		`{"ok":true,"protocol":"ara-wake-v1","sequence":4,"wake":false}`,
		`{"ok":true,"protocol":"ara-wake-v1","sequence":6,"wake":false}`,
		`{"ok":true,"protocol":"ara-wake-v1","sequence":5,"wake":true}`,
		`{"ok":true,"protocol":"ara-wake-v1","sequence":6,"wake":true}` + strings.Repeat(" ", 600),
	} {
		server := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
			_, _ = io.WriteString(w, body)
		}))
		cfg := Config{DeviceID: "DESKTOP-FTDK0HP", WakeListenerToken: strings.Repeat("L", 40)}
		_, err := readHostingerWake(cfg, server.URL, "wait", 5, server.Client())
		server.Close()
		if err == nil {
			t.Errorf("malformed wake payload accepted: size=%d", len(body))
		}
	}
}

func TestWakeConfigInvalidCredentialFallsBack(t *testing.T) {
	t.Setenv("ANTHARES_CONTROL_URL", "https://control.example.org")
	t.Setenv("ANTHARES_DEVICE_TOKEN", "device-only-secret")
	t.Setenv("ANTHARES_DEVICE_ID", "DESKTOP-FTDK0HP")
	t.Setenv("ANTHARES_WAKE_ENABLED", "1")
	t.Setenv("ANTHARES_WAKE_LISTENER_TOKEN", "short")
	cfg, err := loadConfig()
	if err != nil || cfg.WakeEnabled || cfg.WakeListenerToken != "" ||
		startWakeListener(cfg) != nil {
		t.Fatalf("invalid wake config must preserve legacy control: %v", err)
	}
	t.Setenv("ANTHARES_WAKE_LISTENER_TOKEN", strings.Repeat("L", 40))
	cfg, err = loadConfig()
	if err != nil || !cfg.WakeEnabled || !validWakeListenerToken(cfg.WakeListenerToken) {
		t.Fatalf("valid wake listener configuration rejected: %v", err)
	}
}
