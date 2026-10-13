package main

import (
	"errors"
	"os"
	"path/filepath"
	"testing"
)

func TestPermanentResultRejection(t *testing.T) {
	cases := []struct {
		err  error
		want bool
	}{
		{errors.New("result status 404"), true},
		{errors.New("result status 409"), true},
		{errors.New("result status 500"), false},
		{errors.New("network timeout"), false},
		{nil, false},
	}
	for _, tc := range cases {
		if got := permanentResultRejection(tc.err); got != tc.want {
			t.Fatalf("permanentResultRejection(%v)=%v want %v", tc.err, got, tc.want)
		}
	}
}

func TestQuarantineRejectedResultPreservesArtifact(t *testing.T) {
	dir := t.TempDir()
	pending := filepath.Join(dir, "job123.pending")
	if err := os.WriteFile(pending, []byte("encrypted-audit"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := quarantineRejectedResult(pending); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(pending); !os.IsNotExist(err) {
		t.Fatalf("pending artifact still exists: %v", err)
	}
	rejected := filepath.Join(dir, "job123.rejected")
	got, err := os.ReadFile(rejected)
	if err != nil {
		t.Fatal(err)
	}
	if string(got) != "encrypted-audit" {
		t.Fatalf("quarantined artifact changed: %q", got)
	}
}
