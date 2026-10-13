package main

import (
    "errors"
    "os"
    "path/filepath"
    "strings"
)

// securePath first enforces the configured lexical roots, then rejects traversal
// through existing symlinks/reparse-like path components. Missing leaf components
// are allowed so authorized files/directories can still be created.
func securePath(cfg Config, path string) (string, error) {
    if len(cfg.AllowedRoots) == 0 {
        return "", errors.New("file access disabled; ANTHARES_ALLOWED_ROOTS is empty")
    }
    abs, err := filepath.Abs(path)
    if err != nil {
        return "", err
    }
    abs = filepath.Clean(abs)

    allowed := false
    lower := strings.ToLower(abs)
    for _, root := range cfg.AllowedRoots {
        r := strings.ToLower(filepath.Clean(root))
        if lower == r || strings.HasPrefix(lower, r+string(os.PathSeparator)) {
            allowed = true
            break
        }
    }
    if !allowed {
        return "", errors.New("path outside allowed roots")
    }

    // Walk every existing component. On Go/Windows, symlinks and junction-like
    // reparse points surfaced as ModeSymlink are rejected. EvalSymlinks provides
    // a second containment check for existing paths.
    volume := filepath.VolumeName(abs)
    rest := strings.TrimPrefix(abs, volume)
    current := volume + string(os.PathSeparator)
    for _, part := range strings.Split(rest, string(os.PathSeparator)) {
        if part == "" {
            continue
        }
        current = filepath.Join(current, part)
        info, err := os.Lstat(current)
        if os.IsNotExist(err) {
            break
        }
        if err != nil {
            return "", err
        }
        if info.Mode()&os.ModeSymlink != 0 {
            return "", errors.New("path contains symbolic link or reparse point")
        }
    }

    if _, err := os.Lstat(abs); err == nil {
        resolved, err := filepath.EvalSymlinks(abs)
        if err != nil {
            return "", err
        }
        resolved, err = filepath.Abs(resolved)
        if err != nil {
            return "", err
        }
        rl := strings.ToLower(filepath.Clean(resolved))
        contained := false
        for _, root := range cfg.AllowedRoots {
            rr := strings.ToLower(filepath.Clean(root))
            if rl == rr || strings.HasPrefix(rl, rr+string(os.PathSeparator)) {
                contained = true
                break
            }
        }
        if !contained {
            return "", errors.New("resolved path outside allowed roots")
        }
    }
    return abs, nil
}

// Compatibility alias used by direct read/write call sites.
func safeExistingPath(cfg Config, path string) (string, error) {
    return securePath(cfg, path)
}
