package main

// Wake notifications are hints, never a command source. Only the pre-existing
// authenticated Vercel HTTP path may lease, execute, or complete a job.
import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math/rand"
	"net"
	"net/http"
	"net/netip"
	"net/url"
	"strings"
	"sync/atomic"
	"time"
)

const (
	araHostingerWakeOrigin       = "https://anthares.us/ara-notify/index.php"
	araHostingerDevice           = "DESKTOP-FTDK0HP"
	araHostingerWaitSeconds      = 20
	araHostingerReadMax          = 1024
	araHostingerConnectedRecheck = 12 * time.Second
	araHostingerLegacyWait       = 2 * time.Second
)

type wakeSubscriber struct {
	online atomic.Bool
	events chan struct{}
}

func newWakeSubscriber() *wakeSubscriber { return &wakeSubscriber{events: make(chan struct{}, 1)} }
func (s *wakeSubscriber) signal() {
	if s == nil {
		return
	}
	select {
	case s.events <- struct{}{}:
	default:
	}
}
func (s *wakeSubscriber) setOnline(v bool) {
	if s == nil {
		return
	}
	if s.online.Swap(v) != v {
		// Existing agent stdout is already supervised. Emit only state changes,
		// never tokens, payloads, URLs or per-request logs.
		if v {
			fmt.Println("ARA_WAKE_MODE=event_12s_reconcile")
		} else {
			fmt.Println("ARA_WAKE_MODE=legacy_2s_fallback")
		}
		s.signal()
	}
}
func wakeWaitDuration(s *wakeSubscriber) time.Duration {
	if s != nil && s.online.Load() {
		return araHostingerConnectedRecheck
	}
	return araHostingerLegacyWait
}
func (s *wakeSubscriber) waitAfterEmpty() {
	wait := wakeWaitDuration(s)
	if s == nil {
		time.Sleep(wait)
		return
	}
	timer := time.NewTimer(wait)
	defer timer.Stop()
	select {
	case <-s.events:
	case <-timer.C:
	}
}

// Verify strictly wake-only JSON, with no embedded command/job/URL, before
// allowing a response to influence the scheduling of the next HTTP lease call.
// A broker restart can legitimately reset its monotonic in-memory sequence.
// Treat that as a listener outage first, then re-synchronize from sequence 0.
// Resynchronization only wakes the existing authenticated Vercel lease path.
var errHostingerSequenceReset = errors.New("wake_sequence_regression")

func decodeHostingerWake(raw []byte, since uint64) (next uint64, wake bool, err error) {
	if len(raw) == 0 || len(raw) > araHostingerReadMax {
		return since, false, errors.New("wake_response_size")
	}
	var fields map[string]json.RawMessage
	if err = json.Unmarshal(raw, &fields); err != nil || fields == nil {
		return since, false, errors.New("wake_response_json")
	}
	for key := range fields {
		switch key {
		case "ok", "protocol", "device_id", "sequence", "wake", "updated_at":
		default:
			return since, false, errors.New("wake_unexpected_field")
		}
	}
	seqRaw, ok := fields["sequence"]
	if !ok {
		return since, false, errors.New("wake_sequence_missing")
	}
	var sequence uint64
	if err = json.Unmarshal(seqRaw, &sequence); err != nil {
		return since, false, errors.New("wake_sequence_invalid")
	}
	if okRaw, has := fields["ok"]; has {
		var accepted bool
		if json.Unmarshal(okRaw, &accepted) != nil || !accepted {
			return since, false, errors.New("wake_not_ok")
		}
	}
	if protocolRaw, has := fields["protocol"]; has {
		var protocol string
		if json.Unmarshal(protocolRaw, &protocol) != nil || protocol != "ara-wake-v1" {
			return since, false, errors.New("wake_protocol_invalid")
		}
	}
	if deviceRaw, has := fields["device_id"]; has {
		var device string
		if json.Unmarshal(deviceRaw, &device) != nil || device != araHostingerDevice {
			return since, false, errors.New("wake_device_mismatch")
		}
	}
	wakeRaw, has := fields["wake"]
	if !has || json.Unmarshal(wakeRaw, &wake) != nil {
		return since, false, errors.New("wake_flag_invalid")
	}
	if sequence < since {
		return since, false, errHostingerSequenceReset
	}
	// Sequence advances are authoritative wake hints even if a buggy old
	// broker returned wake=false; still claim any actual job via Vercel.
	return sequence, wake || sequence > since, nil
}

func hostingerWaitURL(since uint64) string {
	u, _ := url.Parse(araHostingerWakeOrigin)
	q := u.Query()
	q.Set("action", "wait")
	q.Set("device_id", araHostingerDevice)
	q.Set("since", fmt.Sprint(since))
	q.Set("seconds", fmt.Sprint(araHostingerWaitSeconds))
	u.RawQuery = q.Encode()
	return u.String()
}

// A separate, read-only listener credential is required. Never reuse the
// device-control bearer or the publisher's secret. No redirects permitted.
func waitHostinger(ctx context.Context, client *http.Client, token string, since uint64) (uint64, bool, error) {
	if len(token) < 32 || strings.ContainsAny(token, "\r\n\t ") {
		return since, false, errors.New("wake_listener_key_unconfigured")
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, hostingerWaitURL(since), nil)
	if err != nil {
		return since, false, err
	}
	req.Header.Set("X-Anthares-Notify-Key", token)
	req.Header.Set("Accept", "application/json")
	req.Header.Set("User-Agent", "AntharesARA-WakeListener/1.0")
	resp, err := client.Do(req)
	if err != nil {
		return since, false, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return since, false, fmt.Errorf("wake_http_%d", resp.StatusCode)
	}
	b, err := io.ReadAll(io.LimitReader(resp.Body, araHostingerReadMax+1))
	if err != nil {
		return since, false, err
	}
	return decodeHostingerWake(b, since)
}

func hostingerReconnectDelay(failures int) time.Duration {
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
	return base + time.Duration(rand.Int63n(int64(base/10)+1))
}

// runHostingerWithPolicy exists to exercise deterministic failover transitions.
// The production caller always uses the bounded exponential reconnect policy.
func (s *wakeSubscriber) runHostinger(ctx context.Context, token string, client *http.Client) {
	s.runHostingerWithPolicy(ctx, token, client, hostingerReconnectDelay)
}
func (s *wakeSubscriber) runHostingerWithPolicy(ctx context.Context, token string, client *http.Client, backoff func(int) time.Duration) {
	var since uint64
	failures := 0
	defer s.setOnline(false)
	for ctx.Err() == nil {
		next, wake, err := waitHostinger(ctx, client, token, since)
		if err == nil {
			failures = 0
			s.setOnline(true) // initial handshake triggers immediate queue scan
			since = next
			if wake {
				s.signal()
			}
			continue
		}
		s.setOnline(false) // immediately restore the pre-existing 2s legacy poll
		// On a broker-side sequence reset (service restart), re-register from
		// zero after first switching back to legacy mode. Do not get stuck
		// polling only the obsolete sequence forever.
		if errors.Is(err, errHostingerSequenceReset) {
			since = 0
		}
		failures++
		delay := backoff(failures - 1)
		if delay < 0 {
			delay = 0
		}
		timer := time.NewTimer(delay)
		select {
		case <-ctx.Done():
			timer.Stop()
			return
		case <-timer.C:
		}
	}
}

// Hostinger CDN may refuse webhook-like traffic (HTTP 403). An optional
// fixed, public origin IP lets HTTPS keep the anthares.us Host/SNI and normal
// certificate verification while dialing the server directly.
func publicWakeOrigin(ip string) bool {
	addr, err := netip.ParseAddr(ip)
	if err != nil || !addr.Is4() || !addr.IsGlobalUnicast() || addr.IsPrivate() || addr.IsLoopback() || addr.IsLinkLocalUnicast() {
		return false
	}
	// Exclude CGNAT, test ranges and broadcast-like address families.
	reserved := []netip.Prefix{
		netip.MustParsePrefix("100.64.0.0/10"),
		netip.MustParsePrefix("192.0.0.0/24"),
		netip.MustParsePrefix("192.0.2.0/24"),
		netip.MustParsePrefix("198.51.100.0/24"),
		netip.MustParsePrefix("203.0.113.0/24"),
	}
	for _, r := range reserved {
		if r.Contains(addr) {
			return false
		}
	}
	return true
}
func hostingerWakeClient(originIP string) (*http.Client, error) {
	transport := http.DefaultTransport.(*http.Transport).Clone()
	if originIP != "" {
		if !publicWakeOrigin(originIP) {
			return nil, errors.New("wake_origin_ip_invalid")
		}
		dialer := &net.Dialer{Timeout: 8 * time.Second, KeepAlive: 20 * time.Second}
		transport.DialContext = func(ctx context.Context, network, address string) (net.Conn, error) {
			host, port, err := net.SplitHostPort(address)
			if err != nil || host != "anthares.us" || port != "443" {
				return nil, errors.New("wake_origin_host_mismatch")
			}
			return dialer.DialContext(ctx, "tcp", net.JoinHostPort(originIP, port))
		}
		transport.Proxy = nil // origin IP must never be resolved by a proxy
	}
	return &http.Client{Timeout: 27 * time.Second, Transport: transport,
		CheckRedirect: func(_ *http.Request, _ []*http.Request) error { return http.ErrUseLastResponse }}, nil
}

func startWakeSubscriber(cfg Config) *wakeSubscriber {
	if !cfg.WakeEnabled || cfg.ControlURL == "" || cfg.DeviceID != araHostingerDevice ||
		len(cfg.WakeListenerToken) < 32 || strings.ContainsAny(cfg.WakeListenerToken, "\r\n\t ") {
		return nil
	}
	client, err := hostingerWakeClient(cfg.WakeOriginIP)
	if err != nil {
		return nil
	}
	s := newWakeSubscriber()
	go s.runHostinger(context.Background(), cfg.WakeListenerToken, client)
	return s
}
