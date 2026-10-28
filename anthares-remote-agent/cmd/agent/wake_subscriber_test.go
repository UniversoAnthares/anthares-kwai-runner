package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/gorilla/websocket"
)

func TestWakeFlagAndIdentityFailClosed(t *testing.T) {
	base := Config{
		ControlURL:  "https://anthares-remote-primary.vercel.app",
		DeviceToken: "test-only-example-device-token-length",
		DeviceID:    araWakeDevice,
	}
	if s := startWakeSubscriber(base); s != nil {
		t.Fatal("default-off listener must not start")
	}
	base.WakeEnabled = true
	base.DeviceID = "OTHER-DEVICE"
	if s := startWakeSubscriber(base); s != nil {
		t.Fatal("foreign-device listener must not start")
	}
	base.DeviceID = araWakeDevice
	base.ControlURL = ""
	if s := startWakeSubscriber(base); s != nil {
		t.Fatal("queue-only mode must not start wake transport")
	}
	base.ControlURL = "https://anthares-remote-primary.vercel.app"
	base.DeviceToken = "too-short"
	if s := startWakeSubscriber(base); s != nil {
		t.Fatal("short device credential must not start listener")
	}
	if strings.Contains(araWakeEndpoint, "http://") ||
		!strings.HasPrefix(araWakeEndpoint, "wss://anthares-ara-wake.anthares1.workers.dev/") {
		t.Fatal("wake endpoint is not fixed to trusted TLS origin")
	}
}

func TestWakeIdleReconciliationPolicy(t *testing.T) {
	if d := wakeWaitDuration(nil); d != 2*time.Second {
		t.Fatalf("disabled fallback interval %s", d)
	}
	s := newWakeSubscriber()
	if d := wakeWaitDuration(s); d != 2*time.Second {
		t.Fatalf("disconnected fallback interval %s", d)
	}
	s.setOnline(true)
	select {
	case <-s.events:
	default:
		t.Fatal("socket-ready must trigger immediate queue reconciliation")
	}
	if d := wakeWaitDuration(s); d != 12*time.Second || d >= 31*time.Second {
		t.Fatalf("lost-event reconciliation must beat minimum job expiry: %s", d)
	}
	s.setOnline(false)
	select {
	case <-s.events:
	default:
		t.Fatal("disconnect must wake HTTP loop immediately")
	}
	if d := wakeWaitDuration(s); d != 2*time.Second {
		t.Fatalf("disconnect did not restore legacy interval: %s", d)
	}
	s.signal()
	start := time.Now()
	s.waitAfterEmpty()
	if time.Since(start) > 200*time.Millisecond {
		t.Fatal("a received wake must bypass the idle timer")
	}
}

func TestWakeFramesAreHintsOnly(t *testing.T) {
	now := time.Now()
	ms := now.UnixMilli()
	nonce := "11111111-2222-4333-8444-555555555555"
	cases := []struct {
		name string
		data string
		want string
		ok   bool
	}{
		{"ready", fmt.Sprintf("{\"type\":\"ready\",\"at_ms\":%d}", ms), "ready", true},
		{"wake", fmt.Sprintf("{\"type\":\"wake\",\"at_ms\":%d,\"nonce\":\"%s\"}", ms, nonce), "wake", true},
		{"pong", "pong", "pong", true},
		{"unknown", fmt.Sprintf("{\"type\":\"execute\",\"at_ms\":%d}", ms), "", false},
		{"command_injection", fmt.Sprintf("{\"type\":\"wake\",\"at_ms\":%d,\"nonce\":\"%s\",\"command\":\"shell\"}", ms, nonce), "", false},
		{"job_injection", fmt.Sprintf("{\"type\":\"wake\",\"at_ms\":%d,\"nonce\":\"%s\",\"job_id\":\"malicious\"}", ms, nonce), "", false},
		{"no_nonce", fmt.Sprintf("{\"type\":\"wake\",\"at_ms\":%d}", ms), "", false},
		{"stale", fmt.Sprintf("{\"type\":\"wake\",\"at_ms\":%d,\"nonce\":\"%s\"}", ms-360000, nonce), "", false},
		{"not_json", "invalid json", "", false},
		{"oversize", strings.Repeat("z", 257), "", false},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got, err := validateWakeFrame([]byte(tc.data), now)
			if (err == nil) != tc.ok || got != tc.want {
				t.Fatalf("got=(%s,%v), want=(%s,ok=%t)", got, err, tc.want, tc.ok)
			}
		})
	}
}

func TestWakeSocketReadyWakeAndDisconnect(t *testing.T) {
	const token = "test-only-device-credential-not-production"
	fireWake := make(chan struct{}, 1)
	closeServer := make(chan struct{}, 1)
	upgrade := websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Authorization") != "Bearer "+token {
			http.Error(w, "unauthorized", 401)
			return
		}
		if r.Header.Get("X-Anthares-Device") != araWakeDevice {
			http.Error(w, "wrong_device", 403)
			return
		}
		socket, err := upgrade.Upgrade(w, r, nil)
		if err != nil {
			return
		}
		defer socket.Close()
		if err := socket.WriteJSON(map[string]interface{}{
			"type": "ready", "at_ms": time.Now().UnixMilli(),
		}); err != nil {
			return
		}
		select {
		case <-fireWake:
		case <-time.After(3 * time.Second):
			return
		}
		if err := socket.WriteJSON(map[string]interface{}{
			"type": "wake", "at_ms": time.Now().UnixMilli(),
			"nonce": "11111111-2222-4333-8444-555555555555",
		}); err != nil {
			return
		}
		select {
		case <-closeServer:
		case <-time.After(3 * time.Second):
		}
	}))
	defer server.Close()
	defer close(closeServer)

	dialer := &websocket.Dialer{HandshakeTimeout: time.Second}
	headers := http.Header{}
	headers.Set("Authorization", "Bearer "+token)
	headers.Set("X-Anthares-Device", araWakeDevice)
	socket, _, err := dialer.Dial("ws"+strings.TrimPrefix(server.URL, "http"), headers)
	if err != nil {
		t.Fatalf("local mock websocket failed: %v", err)
	}
	s := newWakeSubscriber()
	done := make(chan error, 1)
	go func() { done <- s.runSocket(socket) }()
	awaitSignal := func(label string) {
		t.Helper()
		select {
		case <-s.events:
		case <-time.After(2 * time.Second):
			t.Fatalf("missing %s event", label)
		}
	}
	awaitSignal("ready/reconcile")
	if !s.online.Load() {
		t.Fatal("ready must transition to live")
	}
	fireWake <- struct{}{}
	awaitSignal("wake")
	if !s.online.Load() {
		t.Fatal("wake must not disconnect the socket")
	}
	closeServer <- struct{}{}
	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatal("disconnect did not terminate read loop")
	}
	awaitSignal("disconnect")
	if s.online.Load() {
		t.Fatal("connection not marked offline")
	}
}

func TestWakeReconnectBackoffIsBounded(t *testing.T) {
	for _, n := range []int{-1, 0, 1, 4, 10, 100} {
		d := wakeReconnectDelay(n, func(int64) int64 { return 0 })
		if d < 2*time.Second || d > 30*time.Second {
			t.Fatalf("out of bounds for failure %d: %s", n, d)
		}
	}
	if d := wakeReconnectDelay(100, func(max int64) int64 { return max - 1 }); d > 33*time.Second {
		t.Fatalf("jitter exceeded cap: %s", d)
	}
}
