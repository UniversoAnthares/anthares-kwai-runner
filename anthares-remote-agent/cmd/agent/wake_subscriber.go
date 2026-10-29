package main

// Wake hints only. The authoritative command lease and idempotency stay on
// the existing Vercel/Neon HTTP path; GitHub/GitLab consumers are untouched.
import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"
	"math/rand"
	"net/http"
	"net/url"
	"os"
	"regexp"
	"strconv"
	"sync/atomic"
	"time"
)

const (
	araWakeDevice = "DESKTOP-FTDK0HP"
	araWakeEndpoint = "https://anthares.us/ara-notify/index.php"
	araLegacyIdleWait = 2 * time.Second
	araConnectedRecheck = 12 * time.Second
	araWakeMaxFrame = 512
)

var araListenerToken = regexp.MustCompile("^[A-Za-z0-9_-]{32,128}$")

type wakeSubscriber struct {
	online atomic.Bool
	events chan struct{}
}

func newWakeSubscriber() *wakeSubscriber {
	return &wakeSubscriber{events: make(chan struct{}, 1)}
}

func (s *wakeSubscriber) signal() {
	select { case s.events <- struct{}{}: default: }
}

func (s *wakeSubscriber) setOnline(connected bool) {
	if s.online.Swap(connected) != connected {
		// Both subscription and failure reconcile via the original queue.
		s.signal()
	}
}

func wakeWaitDuration(s *wakeSubscriber) time.Duration {
	if s != nil && s.online.Load() { return araConnectedRecheck }
	return araLegacyIdleWait
}

func (s *wakeSubscriber) waitAfterEmpty() {
	delay := wakeWaitDuration(s)
	if s == nil { time.Sleep(delay); return }
	timer := time.NewTimer(delay)
	defer timer.Stop()
	select { case <-s.events: case <-timer.C: }
}

// Strict schema: notifications cannot carry jobs, commands, leases or URLs.
func parseWakeReceipt(raw []byte, health bool) (int64, bool, error) {
	if len(raw) == 0 || len(raw) > araWakeMaxFrame {
		return 0, false, errors.New("wake_receipt_size")
	}
	var fields map[string]json.RawMessage
	if !uniqueWakeJSON(raw) || json.Unmarshal(raw, &fields) != nil || len(fields) != 4 {
		return 0, false, errors.New("wake_receipt_fields")
	}
	for _, value := range fields {
		if bytes.Equal(bytes.TrimSpace(value), []byte("null")) {
			return 0, false, errors.New("wake_null_field")
		}
	}
	var ok bool
	var protocol string
	var sequence int64
	if json.Unmarshal(fields["ok"], &ok) != nil || !ok ||
		json.Unmarshal(fields["protocol"], &protocol) != nil || protocol != "ara-wake-v1" ||
		json.Unmarshal(fields["sequence"], &sequence) != nil || sequence < 0 ||
		sequence > 999999999999999999 {
		return 0, false, errors.New("wake_receipt_invalid")
	}
	if health {
		var role string
		if json.Unmarshal(fields["role"], &role) != nil || role != "listener" {
			return 0, false, errors.New("wake_listener_role")
		}
		return sequence, false, nil
	}
	var wake bool
	if json.Unmarshal(fields["wake"], &wake) != nil {
		return 0, false, errors.New("wake_flag_invalid")
	}
	return sequence, wake, nil
}

type wakeHTTPError struct { status int }
func (e wakeHTTPError) Error() string { return "wake_http_rejected" }

// A quota/auth rejection ends this subscriber attempt; canonical polling stays
// active. Never leave the failed wake attempt waiting for a quota reset.
func terminalWakeError(err error) bool {
	var status wakeHTTPError
	return errors.As(err, &status) &&
		(status.status == 401 || status.status == 402 ||
		 status.status == 403 || status.status == 429)
}

func fetchWakeReceipt(ctx context.Context, client *http.Client, endpoint, token string,
	health bool, since int64) (int64, bool, error) {
	u, err := url.Parse(endpoint)
	if err != nil { return 0, false, errors.New("wake_endpoint_invalid") }
	query := url.Values{"device_id": {araWakeDevice}}
	if health {
		query.Set("action", "health")
	} else {
		query.Set("action", "wait")
		query.Set("since", strconv.FormatInt(since, 10))
		query.Set("seconds", "20")
	}
	u.RawQuery = query.Encode()
	requestCtx, cancel := context.WithTimeout(ctx, 25*time.Second)
	defer cancel()
	req, err := http.NewRequestWithContext(requestCtx, http.MethodGet, u.String(), nil)
	if err != nil { return 0, false, errors.New("wake_request_invalid") }
	// This is the broker LISTENER token, never the publisher or device token.
	req.Header.Set("X-Anthares-Notify-Key", token)
	req.Header.Set("Accept", "application/json")
	req.Header.Set("Cache-Control", "no-store")
	response, err := client.Do(req)
	if err != nil { return 0, false, errors.New("wake_transport_unavailable") }
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK {
		return 0, false, wakeHTTPError{response.StatusCode}
	}
	raw, err := io.ReadAll(io.LimitReader(response.Body, araWakeMaxFrame+1))
	if err != nil { return 0, false, errors.New("wake_read_failed") }
	sequence, wake, err := parseWakeReceipt(raw, health)
	if err != nil { return 0, false, err }
	if !health && (sequence < since || wake != (sequence > since)) {
		return 0, false, errors.New("wake_sequence_inconsistent")
	}
	return sequence, wake, nil
}

func wakeReconnectDelay(failures int, jitter func(int64) int64) time.Duration {
	if failures < 0 { failures = 0 }
	if failures > 4 { failures = 4 }
	base := (2 * time.Second) << failures
	if base > 30*time.Second { base = 30 * time.Second }
	if jitter == nil { jitter = rand.Int63n }
	return base + time.Duration(jitter(int64(base/10)+1))
}

func (s *wakeSubscriber) runLongPoll(ctx context.Context, client *http.Client,
	endpoint, token string) error {
	defer s.setOnline(false)
	sequence, _, err := fetchWakeReceipt(ctx, client, endpoint, token, true, 0)
	if err != nil { return err }
	s.setOnline(true) // Immediate canonical scan covers pre-subscription jobs.
	for ctx.Err() == nil {
		next, wake, err := fetchWakeReceipt(ctx, client, endpoint, token, false, sequence)
		if err != nil { return err }
		if wake { s.signal() }
		sequence = next // Duplicate/coalesced events never execute a job here.
	}
	return ctx.Err()
}

func (s *wakeSubscriber) run(ctx context.Context, client *http.Client,
	endpoint, token string) {
	defer client.CloseIdleConnections()
	for failures := 0; ctx.Err() == nil; failures++ {
		err := s.runLongPoll(ctx, client, endpoint, token)
		if terminalWakeError(err) || ctx.Err() != nil { return }
		timer := time.NewTimer(wakeReconnectDelay(failures, nil))
		select {
		case <-ctx.Done(): timer.Stop(); return
		case <-timer.C:
		}
	}
}

func startWakeSubscriber(cfg Config) *wakeSubscriber {
	if !cfg.WakeEnabled || cfg.ControlURL == "" || cfg.DeviceID != araWakeDevice {
		return nil
	}
	token := os.Getenv("ANTHARES_WAKE_LISTENER_TOKEN")
	if !araListenerToken.MatchString(token) || token == cfg.DeviceToken {
		return nil
	}
	client := &http.Client{
		Timeout: 25 * time.Second,
		CheckRedirect: func(_ *http.Request, _ []*http.Request) error {
			return http.ErrUseLastResponse
		},
	}
	s := newWakeSubscriber()
	go s.run(context.Background(), client, araWakeEndpoint, token)
	return s
}

// Reject duplicate JSON members; json.Unmarshal alone accepts them silently.
func uniqueWakeJSON(raw []byte) bool {
	decoder := json.NewDecoder(bytes.NewReader(raw))
	first, err := decoder.Token()
	if err != nil || first != json.Delim('{') { return false }
	seen := map[string]bool{}
	for decoder.More() {
		key, err := decoder.Token()
		name, ok := key.(string)
		if err != nil || !ok || seen[name] { return false }
		seen[name] = true
		var value json.RawMessage
		if decoder.Decode(&value) != nil { return false }
	}
	if _, err := decoder.Token(); err != nil { return false }
	return decoder.Decode(new(any)) == io.EOF
}
