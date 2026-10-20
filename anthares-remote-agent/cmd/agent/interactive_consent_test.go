package main

import "testing"

func TestActiveDesktopOperationsRequireOwnerAuthorization(t *testing.T) {
    for _, action := range []string{"screenshot", "clipboard_get", "clipboard_set"} {
        if !interactiveSurfaceRequiresOwnerConsent(action) {
            t.Fatalf("%s unexpectedly allowed without owner consent", action)
        }
    }
    for _, action := range []string{"agent_health", "shell", "file_read", "file_write", "process_list"} {
        if interactiveSurfaceRequiresOwnerConsent(action) {
            t.Fatalf("%s should not be blocked as active desktop action", action)
        }
    }
}
