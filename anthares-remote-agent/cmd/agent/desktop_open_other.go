//go:build !windows

package main

import "errors"

func desktopOpen(req desktopOpenRequest) (string, error) {
    return "", errors.New("interactive desktop launch is only supported on Windows")
}
