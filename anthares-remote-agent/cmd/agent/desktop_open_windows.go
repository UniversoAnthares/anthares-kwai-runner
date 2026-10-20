//go:build windows

package main

import (
    "encoding/json"
    "errors"
    "fmt"
    "os"
    "path/filepath"
    "strings"
    "syscall"
    "unsafe"
)

var (
    kernel32Desktop = syscall.NewLazyDLL("kernel32.dll")
    wtsapiDesktop = syscall.NewLazyDLL("wtsapi32.dll")
    advapiDesktop = syscall.NewLazyDLL("advapi32.dll")
    activeConsoleSession = kernel32Desktop.NewProc("WTSGetActiveConsoleSessionId")
    querySessionToken = wtsapiDesktop.NewProc("WTSQueryUserToken")
    createProcessAsUser = advapiDesktop.NewProc("CreateProcessAsUserW")
)

const (
    startfUseShowWindow = 0x00000001
    createNoWindowDesktop = 0x08000000
)

func isolatedChromeRoot(profile string) string {
    // NEVER reuse the user's live Chrome user-data-dir. A second Chrome instance
    // using that root may forward a URL to an already occupied visible window.
    folder := strings.ReplaceAll(profile, " ", "")
    return filepath.Join(`C:\Users\Lucas\AppData\Local\AntharesRemote\HeadlessChrome`, folder)
}

func desktopChromeCommandLine(chrome string, req desktopOpenRequest) string {
    // Both CLI and Windows startup flags are necessary. The session is
    // isolated from existing Chrome and cannot inherit personal cookies.
    args := []string{
        chrome,
        "--headless=new",
        "--mute-audio",
        "--disable-audio-output",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-notifications",
        "--disable-extensions",
        "--disable-sync",
        "--user-data-dir=" + isolatedChromeRoot(req.Profile),
        req.URL,
    }
    quoted := make([]string, 0, len(args))
    for _, arg := range args {
        quoted = append(quoted, syscall.EscapeArg(arg))
    }
    return strings.Join(quoted, " ")
}

func desktopOpen(req desktopOpenRequest) (string, error) {
    if err := validateDesktopOpen(req); err != nil {
        return "", err
    }
    // Do not focus or enumerate occupied user windows, or inject any input.
    // Windows user token is used solely for a new isolated headless process.
    sessionID, _, _ := activeConsoleSession.Call()
    if sessionID == 0 || sessionID == 0xffffffff {
        return "", errors.New("no interactive console session available")
    }
    var token syscall.Handle
    success, _, queryErr := querySessionToken.Call(sessionID, uintptr(unsafe.Pointer(&token)))
    if success == 0 {
        return "", fmt.Errorf("cannot obtain user token for isolated browser: %v", queryErr)
    }
    defer syscall.CloseHandle(token)

    chrome := `C:\Program Files\Google\Chrome\Application\chrome.exe`
    if _, err := os.Stat(chrome); err != nil {
        return "", fmt.Errorf("approved Chrome executable missing: %w", err)
    }
    isolated := isolatedChromeRoot(req.Profile)
    if err := os.MkdirAll(isolated, 0700); err != nil {
        return "", fmt.Errorf("cannot create isolated browser data directory: %w", err)
    }
    app, err := syscall.UTF16PtrFromString(chrome)
    if err != nil {
        return "", err
    }
    cmd, err := syscall.UTF16PtrFromString(desktopChromeCommandLine(chrome, req))
    if err != nil {
        return "", err
    }
    var startup syscall.StartupInfo
    startup.Cb = uint32(unsafe.Sizeof(startup))
    startup.Desktop, _ = syscall.UTF16PtrFromString(`winsta0\default`)
    startup.Flags = startfUseShowWindow
    startup.ShowWindow = 0 // SW_HIDE

    var process syscall.ProcessInformation
    created, _, createErr := createProcessAsUser.Call(
        uintptr(token), uintptr(unsafe.Pointer(app)), uintptr(unsafe.Pointer(cmd)),
        0, 0, 0, createNoWindowDesktop, 0, 0,
        uintptr(unsafe.Pointer(&startup)), uintptr(unsafe.Pointer(&process)),
    )
    if created == 0 {
        return "", fmt.Errorf("cannot launch isolated headless browser: %v", createErr)
    }
    defer syscall.CloseHandle(process.Process)
    defer syscall.CloseHandle(process.Thread)
    result, _ := json.Marshal(map[string]any{
        "ok": true,
        "state": "headless_process_started_not_authenticated",
        "session_id": sessionID,
        "pid": process.ProcessId,
        "profile_label": req.Profile,
        "mode": "invisible_muted_isolated",
        "existing_windows_touched": false,
        "google_session_inherited": false,
        "note": "No Google OAuth consent or ChatGPT plugin account connection was granted",
    })
    return string(result), nil
}
