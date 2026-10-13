package main

import (
	"fmt"
	"os"
	"time"
)

// httpLivenessGuard closes a liveness gap between the queue-aware agent and the
// SYSTEM supervisor. The normal heartbeat loop intentionally keeps the process
// alive while an issue-queue transport is configured. The supervisor, however,
// preserves any existing agent process and therefore cannot recover a process
// whose Cloudflare HTTP transport has become permanently wedged.
//
// Keep the independent issue queues enabled during transient outages, but after
// four consecutive HTTP heartbeat failures terminate this process with the
// documented recovery code. The SYSTEM supervisor restarts a fresh agent and
// reloads both the Cloudflare and issue-queue transports. No remote job is
// replayed automatically: result spooling and issue-queue receipts remain the
// fencing authorities for already-started work.
func init() {
	go func() {
		// Let main load the same environment and finish initial startup first.
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
