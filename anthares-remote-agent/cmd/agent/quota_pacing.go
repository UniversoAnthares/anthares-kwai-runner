package main

import (
	"net/url"
	"strings"
	"time"
)

// controlPollDelay preserves the normal fast path for non-Cloudflare controllers.
// Cloudflare Workers Free charges each incoming request, even cached empty polls.
// Keep the idle/error pacing in the client so requests never reach the Worker.
func controlPollDelay(controlURL string, afterError bool) time.Duration {
	endpoint, err := url.Parse(controlURL)
	isWorkers := err == nil && endpoint.Scheme == "https" &&
		strings.HasSuffix(strings.ToLower(endpoint.Hostname()), ".workers.dev")
	if isWorkers {
		if afterError {
			return 60 * time.Second
		}
		return 15 * time.Second
	}
	if afterError {
		return 3 * time.Second
	}
	return 2 * time.Second
}
