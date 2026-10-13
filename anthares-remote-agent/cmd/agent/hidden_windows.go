//go:build windows

package main

import (
 "context"
 "os/exec"
 "syscall"
)

// hiddenCommandContext prevents child console windows and focus theft.
func hiddenCommandContext(ctx context.Context, name string, args ...string) *exec.Cmd {
 cmd := exec.CommandContext(ctx,name,args...)
 cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow:true, CreationFlags:0x08000000}
 return cmd
}
