package main

import (
	"fmt"
	"os"
	"strings"
	"time"
)

// Guard the HTTP transport only when HTTP control is actually configured.
// In private issue-queue-only mode there is no HTTP endpoint by design, so
// probing an empty URL would create a false failure loop and restart a healthy
// queue worker every minute.
func init() {
	go func() {
		time.Sleep(5 * time.Second)
		cfg, err := loadConfig()
		if err != nil {
			return
		}
		if strings.TrimSpace(cfg.ControlURL) == "" {
			return
		}
		failures := 0
		ticker := time.NewTicker(15 * time.Second)
		defer ticker.Stop()
		for {
			if err := heartbeat(cfg); err != nil {
				failures++
				fmt.Fprintf(os.Stderr, "HTTP liveness guard heartbeat error (%d/4): %v\n", failures, err)
				if failures >= 4 {
					fmt.Fprintln(os.Stderr, "HTTP control remained unavailable; exiting for SYSTEM supervisor recovery")
					os.Exit(23)
				}
			} else {
				failures = 0
			}
			<-ticker.C
		}
	}()
}
