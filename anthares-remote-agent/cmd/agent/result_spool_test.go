package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestEncryptedResultSpoolRoundTripAndTamper(t *testing.T) {
	dir := t.TempDir()
	original := Result{ID: "job_123", OK: true, Output: "private output"}
	if err := saveEncryptedResult(dir, "device-secret", original); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(dir, "job_123.pending")
	ciphertext, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if string(ciphertext) == string([]byte("private output")) {
		t.Fatal("plaintext stored")
	}
	got, err := loadEncryptedResult(path, "device-secret", "job_123")
	if err != nil {
		t.Fatal(err)
	}
	if got.Output != original.Output {
		t.Fatal("roundtrip mismatch")
	}
	if _, err = loadEncryptedResult(path, "wrong-token", "job_123"); err == nil {
		t.Fatal("wrong key accepted")
	}
	ciphertext[len(ciphertext)-1] ^= 1
	if err = os.WriteFile(path, ciphertext, 0600); err != nil {
		t.Fatal(err)
	}
	if _, err = loadEncryptedResult(path, "device-secret", "job_123"); err == nil {
		t.Fatal("tampered result accepted")
	}
}
