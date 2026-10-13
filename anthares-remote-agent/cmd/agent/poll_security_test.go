package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestPollJobRejectsUnsafeControlPayload(t *testing.T) {
	payloads := []string{
		`{"job":{"id":"../escape","type":"ping"}}`,
		`{"job":{"id":"valid-id","type":""}}`,
		`{"job":{"id":"job/route","type":"shell","args":{"command":"echo unsafe"}}}`,
	}
	old := httpClient
	defer func() { httpClient = old }()
	for _, payload := range payloads {
		server := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			_, _ = w.Write([]byte(payload))
		}))
		httpClient = server.Client()
		cfg := Config{ControlURL: server.URL, DeviceToken: "test", DeviceID: "device"}
		job, err := pollJob(cfg)
		server.Close()
		if err == nil || job != nil {
			t.Errorf("unsafe control payload accepted: %s", payload)
		}
	}
}

