package main

import (
	"fmt"
	"os"
	"time"
)

// Keep issue-queue redundancy during transient failures, while ensuring a
// permanently wedged Cloudflare HTTP transport cannot leave an immortal agent
// process that the SYSTEM supervisor refuses to replace.
func init() {
	go func() {
		time.Sleep(5 * time.Second)
		cfg, err := loadConfig()
		if err != nil {
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
