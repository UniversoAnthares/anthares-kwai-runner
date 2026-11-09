package main

import (
	"net/url"
	"math/rand"
	"strings"
	"time"
)

// controlPollDelay preserves the normal fast path for non-Cloudflare controllers.
// Cloudflare Workers Free charges each incoming request, even cached empty polls.
// Keep the idle/error pacing in the client so requests never reach the Worker.
// A 60-second fallback poll cuts idle Worker requests by 75%; authenticated
// WebSocket push remains the immediate-delivery primary transport.
func controlPollDelay(controlURL string, afterError bool) time.Duration {
	endpoint, err := url.Parse(controlURL)
	isWorkers := err == nil && endpoint.Scheme == "https" &&
		strings.HasSuffix(strings.ToLower(endpoint.Hostname()), ".workers.dev")
	if isWorkers {
		if afterError {
			return 60 * time.Second
		}
		return 60 * time.Second
	}
	if afterError {
		return 3 * time.Second
	}
	return 2 * time.Second
}


// controlPollErrorBackoff limits sustained traffic when an HTTP controller
// is unavailable. It is used only in the legacy HTTP fallback transport;
// push mode has no idle polling. Jitter prevents concurrent agents reconnecting
// on the same boundary. The maximum delay is bounded to preserve recovery.
func controlPollErrorBackoff(controlURL string, failures int) time.Duration {
    delay := controlPollDelay(controlURL, true)
    if failures < 1 {failures = 1}
    for i:=1;i<failures && i<5;i++ {
        delay *= 2
        if delay >= 12*time.Minute {delay = 12*time.Minute;break}
    }
    if delay > 12*time.Minute {delay = 12*time.Minute}
    jitter := time.Duration(rand.Int63n(int64(delay/10)+1))
    if delay+jitter > 15*time.Minute {return 15*time.Minute}
    return delay+jitter
}
