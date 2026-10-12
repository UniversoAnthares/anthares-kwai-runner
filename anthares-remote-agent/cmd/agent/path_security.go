package main

import (
 "errors"
 "os"
 "path/filepath"
 "strings"
)

// safeExistingPath rejects reparse-point traversal (including Windows junctions)
// before accessing a file under an authorized root. Callers must still avoid
// concurrent untrusted filesystem mutations between validation and access.
func safeExistingPath(cfg Config, path string) (string, error) {
 p, err := safePath(cfg, path)
 if err != nil { return "", err }
 volume := filepath.VolumeName(p)
 rest := strings.TrimPrefix(p, volume)
 current := volume + string(os.PathSeparator)
 for _, part := range strings.Split(rest, string(os.PathSeparator)) {
  if part == "" { continue }
  current = filepath.Join(current, part)
  info, err := os.Lstat(current)
  if os.IsNotExist(err) { continue }
  if err != nil { return "", err }
  if info.Mode() & os.ModeSymlink != 0 || info.Mode() & os.ModeIrregular != 0 {
   return "", errors.New("path contains link or reparse point")
  }
 }
 return p, nil
}
