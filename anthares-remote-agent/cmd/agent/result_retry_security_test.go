package main

import (
	"testing"
	"time"
)

func TestPostResultRetryInvalidIDFailsWithoutBackoff(t *testing.T) {
	start := time.Now()
	err := postResultRetry(Config{ControlURL: "https://invalid.example", DeviceToken: "secret", DeviceID: "device"}, Result{ID: "../invalid"})
	if err == nil {
		t.Fatal("invalid ID was accepted")
	}
	if time.Since(start) > time.Second {
		t.Fatal("invalid ID triggered retry backoff")
	}
}
