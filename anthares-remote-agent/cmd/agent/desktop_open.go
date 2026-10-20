package main

import (
    "encoding/json"
    "errors"
    "fmt"
    "io"
    "net/url"
    "strings"
)

const desktopOpenPrefix = "ara-desktop-open "

type desktopOpenRequest struct {
    Profile string `json:"profile"`
    URL string `json:"url"`
}

var allowedChromeProfiles = map[string]bool{
    "Default": true,
    "Profile 2": true,
    "Profile 3": true,
    "Profile 5": true,
    "Profile 7": true,
    "Profile 8": true,
    "Profile 9": true,
}

var allowedDesktopHosts = map[string]bool{
    "chatgpt.com": true,
    "accounts.google.com": true,
    "drive.google.com": true,
    "mail.google.com": true,
    "calendar.google.com": true,
    "contacts.google.com": true,
}

func validateDesktopOpen(req desktopOpenRequest) error {
    if !allowedChromeProfiles[req.Profile] {
        return errors.New("desktop profile not authorized")
    }
    if len(req.URL) == 0 || len(req.URL) > 2048 || strings.ContainsAny(req.URL, "\r\n\x00") {
        return errors.New("invalid desktop URL length or characters")
    }
    u, err := url.Parse(req.URL)
    if err != nil || u.Scheme != "https" || !allowedDesktopHosts[strings.ToLower(u.Hostname())] || u.User != nil || u.Opaque != "" || u.Fragment != "" || u.Port() != "" {
        return errors.New("desktop URL must be an approved HTTPS origin without credentials, port or fragment")
    }
    return nil
}

// The signed remote shell entrypoint recognizes this structured request before
// interpreting arbitrary shell commands. Only a fixed installed Chrome binary,
// an existing approved profile, and an allowlisted HTTPS host can be opened.
func maybeHandleDesktopCommand(command string) (bool, string, error) {
    if !strings.HasPrefix(command, desktopOpenPrefix) {
        return false, "", nil
    }
    payload := strings.TrimSpace(strings.TrimPrefix(command, desktopOpenPrefix))
    if len(payload) > 4096 {
        return true, "", errors.New("desktop request too large")
    }
    decoder := json.NewDecoder(strings.NewReader(payload))
    decoder.DisallowUnknownFields()
    var req desktopOpenRequest
    if err := decoder.Decode(&req); err != nil {
        return true, "", fmt.Errorf("invalid desktop request: %w", err)
    }
    var extra any
    if err := decoder.Decode(&extra); err == nil {
        return true, "", errors.New("desktop request must contain one JSON object")
    } else if err != io.EOF {
        return true, "", errors.New("desktop request has trailing data")
    }
    if err := validateDesktopOpen(req); err != nil {
        return true, "", err
    }
    response, err := desktopOpen(req)
    return true, response, err
}
