package main

// The WebSocket transports notifications only. Commands, reservations, leases
// and results still use the original authenticated Vercel/Neon HTTP endpoint.
// It is feature-flagged and introduces no additional Windows process or spool.
import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"math/rand"
	"net/http"
	"regexp"
	"strings"
	"sync/atomic"
	"time"

	"github.com/gorilla/websocket"
)

const (
	araWakeDevice          = "DESKTOP-FTDK0HP"
	araWakeEndpoint        = "wss://anthares-ara-wake.anthares1.workers.dev/connect?device_id=DESKTOP-FTDK0HP"
	araLegacyIdleWait      = 2 * time.Second
	// Even if the socket looks healthy, reconciliation is required because
	// "delivered" does not mean a persisted and acknowledged notification.
	// A job may expire after timeout(>=1s)+30s: 12s remains below this bound.
	araConnectedRecheck   = 12 * time.Second
	araWakePingPeriod     = 35 * time.Second
	araWakeReadDeadline   = 95 * time.Second
	araWakeMaxFrame       = 256
)

var araWakeNonce = regexp.MustCompile("(?i)^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")

type wakeSubscriber struct {
	online atomic.Bool
	events chan struct{}
}

func newWakeSubscriber() *wakeSubscriber {
	return &wakeSubscriber{events: make(chan struct{}, 1)}
}

func (s *wakeSubscriber) signal() {
	select {
	case s.events <- struct{}{}:
	default:
	}
}

func (s *wakeSubscriber) setOnline(connected bool) {
	if s.online.Swap(connected) != connected {
		// Connecting: scan for pre-subscription jobs. Disconnecting:
		// immediately resume the two-second legacy polling interval.
		s.signal()
	}
}

func wakeWaitDuration(s *wakeSubscriber) time.Duration {
	if s != nil && s.online.Load() {
		return araConnectedRecheck
	}
	return araLegacyIdleWait
}

func (s *wakeSubscriber) waitAfterEmpty() {
	delay := wakeWaitDuration(s)
	if s == nil {
		time.Sleep(delay)
		return
	}
	timer := time.NewTimer(delay)
	defer timer.Stop()
	select {
	case <-s.events:
	case <-timer.C:
	}
}

// A wake cannot contain a command, job ID, shell arguments, lease or URL.
func validateWakeFrame(raw []byte, now time.Time) (string, error) {
	if len(raw) == 0 || len(raw) > araWakeMaxFrame {
		return "", errors.New("wake_frame_size_invalid")
	}
	if bytes.Equal(raw, []byte("pong")) {
		return "pong", nil
	}
	var fields map[string]json.RawMessage
	if err := json.Unmarshal(raw, &fields); err != nil {
		return "", errors.New("wake_frame_invalid_json")
	}
	var kind string
	var atMS int64
	if json.Unmarshal(fields["type"], &kind) != nil ||
		json.Unmarshal(fields["at_ms"], &atMS) != nil {
		return "", errors.New("wake_frame_invalid_fields")
	}
	delta := now.UnixMilli() - atMS
	if delta > 300_000 || delta < -300_000 {
		return "", errors.New("wake_frame_stale")
	}
	switch kind {
	case "ready":
		if len(fields) != 2 {
			return "", errors.New("wake_ready_invalid_fields")
		}
		return "ready", nil
	case "wake":
		if len(fields) != 3 {
			return "", errors.New("wake_event_invalid_fields")
		}
		var nonce string
		if json.Unmarshal(fields["nonce"], &nonce) != nil ||
			!araWakeNonce.MatchString(nonce) {
			return "", errors.New("wake_nonce_invalid")
		}
		return "wake", nil
	default:
		return "", errors.New("wake_frame_unknown_type")
	}
}

// A connected WebSocket uses application-level pings, answered by the
// existing Cloudflare DO ("ping" => "pong"); they never query Neon.
func (s *wakeSubscriber) runSocket(conn *websocket.Conn) error {
	defer conn.Close()
	defer s.setOnline(false)
	conn.SetReadLimit(araWakeMaxFrame)
	if err := conn.SetReadDeadline(time.Now().Add(araWakeReadDeadline)); err != nil {
		return err
	}

	stopPing := make(chan struct{})
	defer close(stopPing)
	go func() {
		ticker := time.NewTicker(araWakePingPeriod)
		defer ticker.Stop()
		for {
			select {
			case <-stopPing:
				return
			case <-ticker.C:
				_ = conn.SetWriteDeadline(time.Now().Add(3 * time.Second))
				if err := conn.WriteMessage(websocket.TextMessage, []byte("ping")); err != nil {
					_ = conn.Close()
					return
				}
			}
		}
	}()

	for {
		msgType, payload, err := conn.ReadMessage()
		if err != nil {
			return err
		}
		if msgType != websocket.TextMessage {
			return errors.New("wake_nontext_frame")
		}
		event, err := validateWakeFrame(payload, time.Now())
		if err != nil {
			return err
		}
		if err := conn.SetReadDeadline(time.Now().Add(araWakeReadDeadline)); err != nil {
			return err
		}
		switch event {
		case "ready":
			s.setOnline(true)
		case "wake":
			if !s.online.Load() {
				return errors.New("wake_before_ready")
			}
			s.signal()
		case "pong":
			// Only a liveness signal; not queue work.
		}
	}
}

func wakeReconnectDelay(failures int, jitter func(int64) int64) time.Duration {
	if failures < 0 {
		failures = 0
	}
	if failures > 4 {
		failures = 4
	}
	base := (2 * time.Second) << failures
	if base > 30*time.Second {
		base = 30 * time.Second
	}
	if jitter == nil {
		jitter = rand.Int63n
	}
	return base + time.Duration(jitter(int64(base/10)+1))
}

func (s *wakeSubscriber) run(ctx context.Context, cfg Config, endpoint string,
	dialer *websocket.Dialer) {
	failures := 0
	for ctx.Err() == nil {
		// Do not log the bearer, headers, or network response body.
		headers := http.Header{}
		headers.Set("Authorization", "Bearer "+cfg.DeviceToken)
		headers.Set("X-Anthares-Device", cfg.DeviceID)
		conn, response, err := dialer.DialContext(ctx, endpoint, headers)
		if err == nil {
			failures = 0
			_ = s.runSocket(conn)
		} else if response != nil && response.Body != nil {
			_ = response.Body.Close()
		}
		s.setOnline(false)
		failures++
		timer := time.NewTimer(wakeReconnectDelay(failures-1, nil))
		select {
		case <-ctx.Done():
			timer.Stop()
			return
		case <-timer.C:
		}
	}
}

func startWakeSubscriber(cfg Config) *wakeSubscriber {
	if !cfg.WakeEnabled || cfg.ControlURL == "" || cfg.DeviceID != araWakeDevice {
		return nil
	}
	if len(cfg.DeviceToken) < 20 || strings.ContainsAny(cfg.DeviceToken, "\r\n") {
		return nil
	}
	s := newWakeSubscriber()
	// Fixed, trusted wss:// destination; no arbitrary URL from env or jobs,
	// and no browser/HTTP redirects. OAuth and original control are unchanged.
	dialer := &websocket.Dialer{
		Proxy:             http.ProxyFromEnvironment,
		HandshakeTimeout:  6 * time.Second,
		EnableCompression: false,
	}
	go s.run(context.Background(), cfg, araWakeEndpoint, dialer)
	return s
}
