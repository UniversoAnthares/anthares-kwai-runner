package main

import "testing"

func TestDesktopOpenValidation(t *testing.T) {
    for _, tt := range []struct {
        profile string
        url string
        allowed bool
    }{
        {"Default", "https://chatgpt.com/", true},
        {"Profile 2", "https://chatgpt.com/settings/apps", true},
        {"Profile 9", "https://drive.google.com/drive/my-drive", true},
        {"Profile 14", "https://chatgpt.com/", false},
        {"Profile 20", "https://chatgpt.com/", false},
        {"Default", "https://example.org/", false},
        {"Default", "http://chatgpt.com/", false},
        {"Default", "https://chatgpt.com:444/", false},
    } {
        err := validateDesktopOpen(desktopOpenRequest{Profile: tt.profile, URL: tt.url})
        if (err == nil) != tt.allowed {
            t.Fatalf("unexpected result for %s %s: %v", tt.profile, tt.url, err)
        }
    }
}
