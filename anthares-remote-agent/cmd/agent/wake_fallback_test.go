package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

type scriptedWakeResponse struct {
	status int
	body   string
	err    error
}

func testFallbackClient(steps <-chan scriptedWakeResponse, started chan<- struct{}) *http.Client {
	return &http.Client{Transport: wakeRoundTrip(func(req *http.Request) (*http.Response, error) {
		select {
		case started <- struct{}{}:
		case <-req.Context().Done():
			return nil, req.Context().Err()
		}
		select {
		case step := <-steps:
			if step.err != nil {
				return nil, step.err
			}
			return &http.Response{StatusCode: step.status, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(step.body))}, nil
		case <-req.Context().Done():
			return nil, req.Context().Err()
		}
	}), Timeout: 5 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
}

func mustReceive(t *testing.T, events <-chan struct{}, label string) {
	t.Helper()
	select {
	case <-events:
	case <-time.After(2 * time.Second):
		t.Fatalf("missing wake/fallback signal: %s", label)
	}
}
func mustStarted(t *testing.T, started <-chan struct{}, label string) {
	t.Helper()
	select {
	case <-started:
	case <-time.After(2 * time.Second):
		t.Fatalf("missing long-poll request: %s", label)
	}
}

func TestFallbackTransitions401403503MalformedRecover(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	s := newWakeSubscriber()
	steps := make(chan scriptedWakeResponse)
	started := make(chan struct{})
	client := testFallbackClient(steps, started)
	var reconnectAttempts atomic.Int32
	done := make(chan struct{})
	go func() {
		s.runHostingerWithPolicy(ctx, testListenerToken, client, func(_ int) time.Duration { reconnectAttempts.Add(1); return 0 })
		close(done)
	}()
	// No event source is healthy until a protocol-valid HTTP 200 is decoded.
	if wakeWaitDuration(s) != 2*time.Second {
		t.Fatal("pre-ready legacy fallback missing")
	}
	mustStarted(t, started, "first listener wait")
	steps <- scriptedWakeResponse{200, `{"ok":true,"sequence":0,"wake":false,"protocol":"ara-wake-v1"}`, nil}
	mustReceive(t, s.events, "initial listener ready")
	if !s.online.Load() || wakeWaitDuration(s) != 12*time.Second {
		t.Fatal("valid listener should enable 12-second reconciliation")
	}
	mustStarted(t, started, "subsequent listener wait")
	// Revoked listener token must resume two-second legacy poll with immediate signal.
	steps <- scriptedWakeResponse{401, `{"error":"unauthorized"}`, nil}
	mustReceive(t, s.events, "401 failure fallback")
	if s.online.Load() || wakeWaitDuration(s) != 2*time.Second {
		t.Fatal("401 must restore legacy 2-second poll")
	}
	mustStarted(t, started, "retry after auth error")
	steps <- scriptedWakeResponse{403, `blocked`, nil}
	// Already offline: no additional event needed, but legacy interval stays 2s.
	mustStarted(t, started, "retry after CDN error")
	if s.online.Load() || wakeWaitDuration(s) != 2*time.Second {
		t.Fatal("403 must stay in legacy mode")
	}
	steps <- scriptedWakeResponse{503, `maintenance`, nil}
	mustStarted(t, started, "retry after 503")
	if s.online.Load() {
		t.Fatal("503 must stay offline")
	}
	steps <- scriptedWakeResponse{200, `{"wake":true,"sequence":20,"job_id":"untrusted"}`, nil}
	mustStarted(t, started, "retry after malicious JSON")
	if s.online.Load() {
		t.Fatal("payload injection must not be treated as ready")
	}
	steps <- scriptedWakeResponse{0, "", errors.New("network_lost")}
	mustStarted(t, started, "retry after network loss")
	if s.online.Load() {
		t.Fatal("network error must not be treated as ready")
	}
	steps <- scriptedWakeResponse{200, `{"ok":true,"sequence":21,"wake":true,"protocol":"ara-wake-v1"}`, nil}
	mustReceive(t, s.events, "broker recovery")
	if !s.online.Load() || wakeWaitDuration(s) != 12*time.Second {
		t.Fatal("healthy broker recovery not restored")
	}
	mustStarted(t, started, "next idle wait")
	// A normal timeout (20s with no new event) stays healthy, not a failure.
	steps <- scriptedWakeResponse{200, `{"ok":true,"sequence":21,"wake":false,"protocol":"ara-wake-v1"}`, nil}
	mustStarted(t, started, "successful idle cycle")
	if !s.online.Load() || wakeWaitDuration(s) != 12*time.Second {
		t.Fatal("valid idle response must not spuriously trigger fallback")
	}
	cancel()
	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatal("listener did not cancel promptly")
	}
	if s.online.Load() || wakeWaitDuration(s) != 2*time.Second {
		t.Fatal("cancelled listener remained online")
	}
	if reconnectAttempts.Load() < 5 {
		t.Fatalf("expected bounded reconnect policy on each error, got %d", reconnectAttempts.Load())
	}
	fmt.Println("ARA_ITEM10_BROKER_HTTP_FAILURE_RECOVERY_LEGACY_2S_PASS")
}

func TestFallbackBrokerResetRecoversAfterReRegister(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	s := newWakeSubscriber()
	steps := make(chan scriptedWakeResponse)
	started := make(chan struct{})
	seenSince := make(chan string, 8)
	client := &http.Client{Transport: wakeRoundTrip(func(req *http.Request) (*http.Response, error) {
		select {
		case started <- struct{}{}:
		case <-req.Context().Done():
			return nil, req.Context().Err()
		}
		seenSince <- req.URL.Query().Get("since")
		select {
		case item := <-steps:
			return &http.Response{StatusCode: item.status, Body: io.NopCloser(strings.NewReader(item.body)), Header: http.Header{}}, nil
		case <-req.Context().Done():
			return nil, req.Context().Err()
		}
	}), Timeout: 5 * time.Second}
	done := make(chan struct{})
	go func() {
		s.runHostingerWithPolicy(ctx, testListenerToken, client, func(int) time.Duration { return 0 })
		close(done)
	}()
	mustStarted(t, started, "first wait")
	if v := <-seenSince; v != "0" {
		t.Fatalf("want initial sequence zero: %q", v)
	}
	steps <- scriptedWakeResponse{200, `{"ok":true,"wake":false,"sequence":31}`, nil}
	mustReceive(t, s.events, "first wake hint / ready")
	mustStarted(t, started, "second wait")
	if v := <-seenSince; v != "31" {
		t.Fatalf("did not retain original sequence: %q", v)
	}
	steps <- scriptedWakeResponse{200, `{"ok":true,"wake":false,"sequence":0}`, nil}
	// The previous 31->0 observation must mark the broker offline immediately.
	// A stale initial wake can remain coalesced, so inspect online after the
	// next reconnect request started (which requires regression processing).
	mustStarted(t, started, "reconnect after sequence reset")
	if s.online.Load() || wakeWaitDuration(s) != 2*time.Second {
		t.Fatal("sequence reset did not trigger legacy fallback")
	}
	if v := <-seenSince; v != "0" {
		t.Fatalf("sequence reset did not re-register from zero: %q", v)
	}
	steps <- scriptedWakeResponse{200, `{"ok":true,"wake":false,"sequence":0}`, nil}
	mustStarted(t, started, "post-recovery wait")
	if !s.online.Load() || wakeWaitDuration(s) != 12*time.Second {
		t.Fatal("broker reset did not recover")
	}
	if v := <-seenSince; v != "0" {
		t.Fatalf("recovered broker sequence incorrect: %q", v)
	}
	cancel()
	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatal("broker reset listener did not stop")
	}
	fmt.Println("ARA_ITEM10_BROKER_SEQUENCE_RESET_RESUBSCRIBE_PASS")
}

func TestFallbackFromFailedListenerDuringIdleSleep(t *testing.T) {
	s := newWakeSubscriber()
	s.setOnline(true)
	mustReceive(t, s.events, "ready signal")
	done := make(chan time.Duration, 1)
	go func() { start := time.Now(); s.waitAfterEmpty(); done <- time.Since(start) }()
	// The sleeper may not yet have entered select; state transition is buffered.
	s.setOnline(false)
	select {
	case elapsed := <-done:
		if elapsed > time.Second {
			t.Fatalf("fallback took %s to stop idle sleep", elapsed)
		}
	case <-time.After(time.Second):
		t.Fatal("failed listener did not interrupt 12s idle wait")
	}
	if wakeWaitDuration(s) != 2*time.Second {
		t.Fatal("legacy idle policy not selected")
	}
	fmt.Println("ARA_ITEM10_DISCONNECT_PREEMPTS_IDLE_RECONCILIATION_PASS")
}

func TestFallbackInvalidOriginConfigIsDefaultLegacy(t *testing.T) {
	values := []struct {
		enabled       bool
		token, origin string
	}{
		{false, testListenerToken, ""}, {true, "", ""}, {true, "not-a-token", ""},
		{true, testListenerToken, "127.0.0.1"}, {true, testListenerToken, "169.254.22.12"},
	}
	for _, v := range values {
		cfg := Config{ControlURL: "https://anthares-remote-primary.vercel.app", DeviceID: araHostingerDevice,
			WakeEnabled: v.enabled, WakeListenerToken: v.token, WakeOriginIP: v.origin}
		listener := startWakeSubscriber(cfg)
		if listener != nil {
			t.Fatalf("invalid wake config launched listener: %+v", v)
		}
		if wakeWaitDuration(listener) != 2*time.Second {
			t.Fatal("invalid wake config must retain legacy poll")
		}
	}
	fmt.Println("ARA_ITEM10_DISABLED_INVALID_LISTENER_LEGACY_2S_PASS")
}

func TestFallbackRefusesRedirectAndInvalidSeqWithoutLosingPriorSeq(t *testing.T) {
	c := testClient(func(r *http.Request) (*http.Response, error) {
		return &http.Response{StatusCode: http.StatusFound, Header: http.Header{"Location": []string{"https://attacker.test"}}, Body: io.NopCloser(strings.NewReader(""))}, nil
	})
	seq, wake, err := waitHostinger(context.Background(), c, testListenerToken, 29)
	if err == nil || seq != 29 || wake {
		t.Fatal("redirect should fail closed without changing sequence")
	}
	bad := testClient(func(r *http.Request) (*http.Response, error) {
		return &http.Response{StatusCode: 200, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(`{"wake":true,"sequence":28}`))}, nil
	})
	seq, wake, err = waitHostinger(context.Background(), bad, testListenerToken, 29)
	if err == nil || seq != 29 || wake {
		t.Fatal("regressed sequence should fail closed and trigger legacy fallback")
	}
	fmt.Println("ARA_ITEM10_REDIRECT_AND_SEQUENCE_REGRESSION_FALLBACK_PASS")
}
