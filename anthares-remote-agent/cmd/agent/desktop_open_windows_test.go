//go:build windows

package main

import (
    "strings"
    "testing"
)

func TestHeadlessChromeNeverUsesOccupiedProfiles(t *testing.T) {
    for _, profile := range []string{"Default","Profile 2","Profile 3","Profile 5","Profile 7","Profile 8","Profile 9"} {
        req := desktopOpenRequest{Profile: profile, URL: "https://chatgpt.com/"}
        args := desktopChromeCommandLine("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", req)
        for _, flag := range []string{"--headless=new", "--mute-audio", "--disable-audio-output", "--disable-notifications", "--disable-sync", "--user-data-dir="} {
            if !strings.Contains(args, flag) {t.Errorf("profile %s missing enforced flag %s",profile,flag)}
        }
        if strings.Contains(args,"--profile-directory") || strings.Contains(args,"--user-data-dir=C:\\Users\\Lucas\\AppData\\Local\\Google\\Chrome\\User Data") {
            t.Errorf("profile %s reused occupied Chrome profile",profile)
        }
        if !strings.Contains(isolatedChromeRoot(profile),"HeadlessChrome") {
            t.Errorf("profile %s has no isolated browser root",profile)
        }
    }
}
