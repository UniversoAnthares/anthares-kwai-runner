package main

// The remote agent cannot independently infer that the owner has authorized
// touching an occupied window. Until a separate authenticated, scoped,
// short-lived consent channel is installed, these jobs fail closed.
func interactiveSurfaceRequiresOwnerConsent(jobType string) bool {
    switch jobType {
    case "screenshot", "clipboard_get", "clipboard_set":
        return true
    default:
        return false
    }
}
