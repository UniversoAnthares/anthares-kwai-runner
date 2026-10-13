package main

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
)

func pathWithin(path, root string) bool {
	p := filepath.Clean(path)
	r := filepath.Clean(root)
	if runtime.GOOS == "windows" {
		p = strings.ToLower(p)
		r = strings.ToLower(r)
	}
	return p == r || strings.HasPrefix(p, r+string(os.PathSeparator))
}

func canonicalRoot(root string) string {
	cleaned := filepath.Clean(root)
	resolved, err := filepath.EvalSymlinks(cleaned)
	if err != nil {
		return cleaned
	}
	abs, err := filepath.Abs(resolved)
	if err != nil {
		return cleaned
	}
	return filepath.Clean(abs)
}

// securePath enforces configured lexical roots and rejects traversal through
// existing symbolic-link/reparse-like components. Missing leaf components are
// allowed so authorized files and directories can be created.
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
	for _, root := range cfg.AllowedRoots {
		if pathWithin(abs, root) {
			allowed = true
			break
		}
	}
	if !allowed {
		return "", errors.New("path outside allowed roots")
	}

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
		if info.Mode()&os.ModeSymlink != 0 || info.Mode()&os.ModeIrregular != 0 {
			return "", errors.New("path contains symbolic link or irregular component")
		}
		// Every existing ancestor must be a directory. The final component may
		// be a regular file because callers often validate a file path.
		if current != abs && !info.IsDir() {
			return "", fmt.Errorf("non-directory component in path: %s", current)
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
		contained := false
		for _, root := range cfg.AllowedRoots {
			if pathWithin(resolved, canonicalRoot(root)) {
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

func safeExistingPath(cfg Config, path string) (string, error) {
	return securePath(cfg, path)
}
