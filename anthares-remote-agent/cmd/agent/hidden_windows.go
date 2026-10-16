//go:build windows

package main

import (
	"context"
	"errors"
	"os"
	"os/exec"
	"strconv"
	"syscall"
	"time"
)

const createNoWindow = 0x08000000

func hiddenSysProcAttr() *syscall.SysProcAttr {
	return &syscall.SysProcAttr{HideWindow: true, CreationFlags: createNoWindow}
}

// hiddenCommandContext prevents child console windows and focus theft.
//
// On Windows, os/exec.CommandContext normally terminates only the direct child.
// Commands such as PowerShell can spawn grandchildren (for example memuc.exe)
// that inherit stdout/stderr handles. If the parent is killed on deadline while
// such a grandchild survives, Cmd.Wait can remain blocked waiting for inherited
// pipe handles to close. That stalls one Anthares Remote execution slot and can
// eventually stop queue consumption entirely.
//
// Override Cancel so a deadline terminates the complete process tree, and set a
// bounded WaitDelay as a final guard against inherited handles that do not close.
func hiddenCommandContext(ctx context.Context, name string, args ...string) *exec.Cmd {
	cmd := exec.CommandContext(ctx, name, args...)
	cmd.SysProcAttr = hiddenSysProcAttr()
	cmd.WaitDelay = 5 * time.Second
	cmd.Cancel = func() error {
		if cmd.Process == nil {
			return os.ErrProcessDone
		}
		killer := exec.Command("taskkill", "/PID", strconv.Itoa(cmd.Process.Pid), "/T", "/F")
		killer.SysProcAttr = hiddenSysProcAttr()
		if err := killer.Run(); err != nil {
			if killErr := cmd.Process.Kill(); killErr != nil && !errors.Is(killErr, os.ErrProcessDone) {
				return killErr
			}
		}
		return nil
	}
	return cmd
}
