package main

import (
	"errors"
	"regexp"
	"strings"
)

// Defense in depth: reject common UI/focus automation at the command entrypoint.
// Explicitly hidden PowerShell child processes are permitted because they are
// the supported non-interactive maintenance primitive for SYSTEM recovery.
var interactiveCommandPatterns = []*regexp.Regexp{
	regexp.MustCompile(`(?i)\b(sendkeys|sendinput|setforegroundwindow|showwindow|switchto|appactivate|wscript\.shell|pyautogui|pynput|autohotkey|nircmd|xdotool)\b`),
	regexp.MustCompile(`(?i)\b(start-process|start)\b[^\r\n]*(?:-windowstyle\s+(?:normal|maximized|minimized)|\b(?:chrome|msedge|firefox|notepad|explorer|cmd|powershell)\.exe\b)`),
	regexp.MustCompile(`(?i)\b(?:user32\.dll|mouse_event|keybd_event|setcursorpos|clickinput)\b`),
}

var hiddenPowerShellStart = regexp.MustCompile(`(?i)\bstart-process\s+(?:powershell(?:\.exe)?|['\"]powershell(?:\.exe)?['\"])[^\r\n]*-windowstyle\s+hidden\b`)

func rejectInteractiveCommand(command string) error {
	if strings.TrimSpace(command) == "" {
		return errors.New("empty command")
	}
	// This exception remains headless: it permits only a PowerShell child that
	// explicitly requests Hidden. UI/focus APIs are still rejected below.
	if hiddenPowerShellStart.MatchString(command) {
		for _, pattern := range []*regexp.Regexp{interactiveCommandPatterns[0], interactiveCommandPatterns[2]} {
			if pattern.MatchString(command) {
				return errors.New("interactive desktop or focus manipulation forbidden by ARA headless policy")
			}
		}
		return nil
	}
	for _, pattern := range interactiveCommandPatterns {
		if pattern.MatchString(command) {
			return errors.New("interactive desktop or focus manipulation forbidden by ARA headless policy")
		}
	}
	return nil
}
