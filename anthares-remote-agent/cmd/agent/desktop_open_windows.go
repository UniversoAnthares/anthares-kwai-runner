//go:build windows

package main

import (
    "encoding/json"
    "errors"
    "fmt"
    "os"
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

func desktopOpen(req desktopOpenRequest) (string, error) {
    // SYSTEM runs in session 0; launch only with the real console user's token.
    sessionID, _, _ := activeConsoleSession.Call()
    if sessionID == 0 || sessionID == 0xffffffff {
        return "", errors.New("no interactive console session available")
    }
    var token syscall.Handle
    success, _, queryErr := querySessionToken.Call(sessionID, uintptr(unsafe.Pointer(&token)))
    if success == 0 {
        return "", fmt.Errorf("cannot obtain active desktop user token: %v", queryErr)
    }
    defer syscall.CloseHandle(token)

    chrome := `C:\Program Files\Google\Chrome\Application\chrome.exe`
    if _, err := os.Stat(chrome); err != nil {
        return "", fmt.Errorf("approved Chrome executable missing: %w", err)
    }
    profileRoot := `C:\Users\Lucas\AppData\Local\Google\Chrome\User Data`
    if _, err := os.Stat(profileRoot); err != nil {
        return "", fmt.Errorf("Chrome user-data directory missing: %w", err)
    }
    app, err := syscall.UTF16PtrFromString(chrome)
    if err != nil {
        return "", err
    }
    commandLine := syscall.EscapeArg(chrome) + " --user-data-dir=" + syscall.EscapeArg(profileRoot) +
        " --profile-directory=" + syscall.EscapeArg(req.Profile) + " " + syscall.EscapeArg(req.URL)
    cmd, err := syscall.UTF16PtrFromString(commandLine)
    if err != nil {
        return "", err
    }
    var startup syscall.StartupInfo
    startup.Cb = uint32(unsafe.Sizeof(startup))
    startup.Desktop, _ = syscall.UTF16PtrFromString(`winsta0\default`)
    var process syscall.ProcessInformation
    created, _, createErr := createProcessAsUser.Call(
        uintptr(token), uintptr(unsafe.Pointer(app)), uintptr(unsafe.Pointer(cmd)),
        0, 0, 0, 0, 0, 0,
        uintptr(unsafe.Pointer(&startup)), uintptr(unsafe.Pointer(&process)),
    )
    if created == 0 {
        return "", fmt.Errorf("cannot launch browser in active desktop session: %v", createErr)
    }
    defer syscall.CloseHandle(process.Process)
    defer syscall.CloseHandle(process.Thread)
    result, _ := json.Marshal(map[string]any{
        "ok": true, "state": "launched_not_authenticated", "session_id": sessionID,
        "pid": process.ProcessId, "profile": req.Profile,
        "note": "Browser launch does not establish Google OAuth consent or plugin connection",
    })
    return string(result), nil
}
