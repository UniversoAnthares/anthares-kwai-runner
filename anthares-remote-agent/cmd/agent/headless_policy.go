package main

import (
	"errors"
	"regexp"
	"strings"
)

// Defense in depth: reject common UI/focus automation at the command entrypoint.
// This is not a full shell sandbox; OS-level isolation remains mandatory.
var interactiveCommandPatterns = []*regexp.Regexp{
	regexp.MustCompile(`(?i)\b(sendkeys|sendinput|setforegroundwindow|showwindow|switchto|appactivate|wscript\.shell|pyautogui|pynput|autohotkey|nircmd|xdotool)\b`),
	regexp.MustCompile(`(?i)\b(start-process|start)\b[^\r\n]*(?:-windowstyle\s+(?:normal|maximized|minimized)|\b(?:chrome|msedge|firefox|notepad|explorer|cmd|powershell)\.exe\b)`),
	regexp.MustCompile(`(?i)\b(?:user32\.dll|mouse_event|keybd_event|setcursorpos|clickinput)\b`),
}

func rejectInteractiveCommand(command string) error {
	if strings.TrimSpace(command) == "" {
		return errors.New("empty command")
	}
	for _, pattern := range interactiveCommandPatterns {
		if pattern.MatchString(command) {
			return errors.New("interactive desktop or focus manipulation forbidden by ARA headless policy")
		}
	}
	return nil
}
