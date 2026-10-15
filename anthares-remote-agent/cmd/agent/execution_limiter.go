package main

import "sync"

var processExecutionLimiter struct {
	once sync.Once
	ch   chan struct{}
}

// executionSemaphore returns the single process-wide execution budget shared
// by HTTP, GitHub and GitLab transports. All callers use the same configured
// MaxConcurrent value from the same environment.
func executionSemaphore(max int) chan struct{} {
	if max < 1 {
		max = 1
	}
	processExecutionLimiter.once.Do(func() {
		processExecutionLimiter.ch = make(chan struct{}, max)
	})
	return processExecutionLimiter.ch
}
