package main

import (
    "path/filepath"
    "strings"
)

// The generic process_start route is restricted to non-GUI command-line tools.
// Everything else must use a dedicated silent/headless adapter or obtain
// explicit owner approval through a future scoped consent channel.
func knownHeadlessExecutable(path string) bool {
    name := strings.ToLower(filepath.Base(path))
    switch name {
    case "ffmpeg.exe", "ffprobe.exe", "go.exe", "git.exe", "curl.exe":
        return true
    default:
        return false
    }
}
