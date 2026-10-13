package main

import (
    "crypto/sha256"
    "encoding/hex"
    "os"
    "path/filepath"
    "runtime"
    "strings"
    "testing"
)

func testConfig(t *testing.T) (Config, string) {
    t.Helper()
    root := t.TempDir()
    abs, err := filepath.Abs(root)
    if err != nil { t.Fatal(err) }
    return Config{AllowedRoots: []string{abs}}, abs
}

func TestSecurePathAllowsAuthorizedPath(t *testing.T) {
    cfg, root := testConfig(t)
    p := filepath.Join(root, "folder with spaces", "á.txt")
    got, err := securePath(cfg, p)
    if err != nil { t.Fatalf("securePath: %v", err) }
    if got != filepath.Clean(p) { t.Fatalf("got %q want %q", got, filepath.Clean(p)) }
}

func TestSecurePathRejectsOutsideRoot(t *testing.T) {
    cfg, root := testConfig(t)
    outside := filepath.Join(filepath.Dir(root), "outside.txt")
    if _, err := securePath(cfg, outside); err == nil { t.Fatal("expected outside-root rejection") }
}

func TestSecurePathRejectsSymlinkEscape(t *testing.T) {
    if runtime.GOOS == "windows" { t.Skip("Windows symlink creation may require privileges; covered by Windows integration matrix") }
    cfg, root := testConfig(t)
    outside := t.TempDir()
    link := filepath.Join(root, "link")
    if err := os.Symlink(outside, link); err != nil { t.Skipf("symlink unavailable: %v", err) }
    if _, err := securePath(cfg, filepath.Join(link, "escape.txt")); err == nil { t.Fatal("expected symlink rejection") }
}

func TestFilesystemLifecycle(t *testing.T) {
    cfg, root := testConfig(t)
    dir := filepath.Join(root, "nested", "dir")
    if _, err := fileMkdir(cfg, dir); err != nil { t.Fatal(err) }
    src := filepath.Join(dir, "origem.txt")
    data := []byte("Anthares Unicode: ação Ω")
    if _, err := fileWriteAtomic(cfg, src, data); err != nil { t.Fatal(err) }
    sum, err := fileSHA256(cfg, src)
    if err != nil { t.Fatal(err) }
    want := sha256.Sum256(data)
    if sum != hex.EncodeToString(want[:]) { t.Fatalf("sha256 mismatch: %s", sum) }
    copied := filepath.Join(root, "copy.txt")
    if _, err := fileCopy(cfg, src, copied); err != nil { t.Fatal(err) }
    renamed := filepath.Join(root, "renamed.txt")
    if _, err := fileRename(cfg, copied, renamed); err != nil { t.Fatal(err) }
    got, err := os.ReadFile(renamed)
    if err != nil { t.Fatal(err) }
    if string(got) != string(data) { t.Fatalf("content mismatch: %q", got) }
    if _, err := fileRemove(cfg, renamed, false); err != nil { t.Fatal(err) }
    if _, err := os.Stat(renamed); !os.IsNotExist(err) { t.Fatalf("file still exists: %v", err) }
}

func TestFileRemoveRefusesAllowedRoot(t *testing.T) {
    cfg, root := testConfig(t)
    if _, err := fileRemove(cfg, root, true); err == nil { t.Fatal("expected root deletion refusal") }
}

func TestAtomicWriteLimit(t *testing.T) {
    cfg, root := testConfig(t)
    tooLarge := make([]byte, 8*1024*1024+1)
    if _, err := fileWriteAtomic(cfg, filepath.Join(root, "large.bin"), tooLarge); err == nil { t.Fatal("expected size limit") }
}

func TestPathWithinCaseSensitivity(t *testing.T) {
 cfg, root := testConfig(t)
 altered := filepath.Join(filepath.Dir(root), "DIFFERENT-"+filepath.Base(root))
 if pathWithin(altered,root) {t.Fatal("different sibling must not be contained")}
 if runtime.GOOS!="windows" {
  upper := filepath.Join(filepath.Dir(root), strings.ToUpper(filepath.Base(root)))
  if upper!=root && pathWithin(upper,root) {t.Fatal("Linux paths must remain case sensitive")}
 }
 _ = cfg
}
