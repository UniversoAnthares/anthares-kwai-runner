package main

import (
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
)

func fileMkdir(cfg Config, path string) (string, error) {
	p, err := securePath(cfg, path)
	if err != nil {
		return "", err
	}
	if err := os.MkdirAll(p, 0700); err != nil {
		return "", err
	}
	return p, nil
}

func fileRemove(cfg Config, path string, recursive bool) (string, error) {
	p, err := securePath(cfg, path)
	if err != nil {
		return "", err
	}
	for _, root := range cfg.AllowedRoots {
		ar, _ := filepath.Abs(root)
		if pathWithin(ar, p) && pathWithin(p, ar) {
			return "", errors.New("refusing to remove an allowed root")
		}
	}
	if recursive {
		if err := os.RemoveAll(p); err != nil {
			return "", err
		}
	} else if err := os.Remove(p); err != nil {
		return "", err
	}
	return p, nil
}

func fileRename(cfg Config, src, dst string) (string, error) {
	s, err := securePath(cfg, src)
	if err != nil {
		return "", err
	}
	d, err := securePath(cfg, dst)
	if err != nil {
		return "", err
	}
	if err := os.MkdirAll(filepath.Dir(d), 0700); err != nil {
		return "", err
	}
	if err := os.Rename(s, d); err != nil {
		return "", err
	}
	return d, nil
}

func fileCopy(cfg Config, src, dst string) (string, error) {
	s, err := securePath(cfg, src)
	if err != nil {
		return "", err
	}
	d, err := securePath(cfg, dst)
	if err != nil {
		return "", err
	}
	in, err := os.Open(s)
	if err != nil {
		return "", err
	}
	defer in.Close()
	st, err := in.Stat()
	if err != nil {
		return "", err
	}
	if !st.Mode().IsRegular() {
		return "", errors.New("source must be a regular file")
	}
	if err := os.MkdirAll(filepath.Dir(d), 0700); err != nil {
		return "", err
	}
	tmp, err := os.CreateTemp(filepath.Dir(d), ".ara-copy-*")
	if err != nil {
		return "", err
	}
	tmpName := tmp.Name()
	defer os.Remove(tmpName)
	if _, err := io.Copy(tmp, in); err != nil {
		tmp.Close()
		return "", err
	}
	if err := tmp.Sync(); err != nil {
		tmp.Close()
		return "", err
	}
	if err := tmp.Close(); err != nil {
		return "", err
	}
	if err := os.Rename(tmpName, d); err != nil {
		return "", err
	}
	return d, nil
}

func fileSHA256(cfg Config, path string) (string, error) {
	p, err := securePath(cfg, path)
	if err != nil {
		return "", err
	}
	f, err := os.Open(p)
	if err != nil {
		return "", err
	}
	defer f.Close()
	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return "", err
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}

func fileWriteAtomic(cfg Config, path string, data []byte) (string, error) {
	if len(data) > 8*1024*1024 {
		return "", errors.New("atomic write exceeds 8 MiB limit")
	}
	p, err := securePath(cfg, path)
	if err != nil {
		return "", err
	}
	if err := os.MkdirAll(filepath.Dir(p), 0700); err != nil {
		return "", err
	}
	tmp, err := os.CreateTemp(filepath.Dir(p), ".ara-write-*")
	if err != nil {
		return "", err
	}
	tmpName := tmp.Name()
	defer os.Remove(tmpName)
	if _, err := tmp.Write(data); err != nil {
		tmp.Close()
		return "", err
	}
	if err := tmp.Sync(); err != nil {
		tmp.Close()
		return "", err
	}
	if err := tmp.Close(); err != nil {
		return "", err
	}
	if err := os.Rename(tmpName, p); err != nil {
		return "", err
	}
	return fmt.Sprintf("wrote %d bytes atomically", len(data)), nil
}
