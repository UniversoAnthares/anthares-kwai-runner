package main

// CF-07: The sole HTTP heartbeat owner is heartbeatLoop in main.go.
// The previous init() routine independently posted a heartbeat every
// 15 seconds, duplicating requests and restarting a healthy queue agent.
// Push mode uses WebSocket protocol ping/pong and private GitHub/GitLab
// recovery; the HTTP fallback retains one heartbeat per 60 seconds.
