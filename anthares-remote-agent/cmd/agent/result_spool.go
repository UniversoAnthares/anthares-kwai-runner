package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

// saveEncryptedResult writes a result atomically with AES-GCM authenticated
// encryption. The caller must choose a private, device-scoped spool directory.
func saveEncryptedResult(dir, token string, result Result) error {
	if err := validateJobID(result.ID); err != nil {
		return err
	}
	if token == "" {
		return errors.New("missing encryption secret")
	}
	if err := os.MkdirAll(dir, 0700); err != nil {
		return err
	}
	plain, err := json.Marshal(result)
	if err != nil {
		return err
	}
	key := sha256.Sum256([]byte("anthares-ara-result-spool-v1:" + token))
	block, err := aes.NewCipher(key[:])
	if err != nil {
		return err
	}
	aead, err := cipher.NewGCM(block)
	if err != nil {
		return err
	}
	nonce := make([]byte, aead.NonceSize())
	if _, err = io.ReadFull(rand.Reader, nonce); err != nil {
		return err
	}
	data := aead.Seal(nonce, nonce, plain, []byte(result.ID))
	tmp, err := os.CreateTemp(dir, ".pending-*")
	if err != nil {
		return err
	}
	defer os.Remove(tmp.Name())
	if err = tmp.Chmod(0600); err != nil {
		tmp.Close()
		return err
	}
	if _, err = tmp.Write(data); err != nil {
		tmp.Close()
		return err
	}
	if err = tmp.Sync(); err != nil {
		tmp.Close()
		return err
	}
	if err = tmp.Close(); err != nil {
		return err
	}
	return os.Rename(tmp.Name(), filepath.Join(dir, result.ID+".pending"))
}
func loadEncryptedResult(path, token, id string) (Result, error) {
	var result Result
	if err := validateJobID(id); err != nil {
		return result, err
	}
	if token == "" {
		return result, errors.New("missing encryption secret")
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return result, err
	}
	key := sha256.Sum256([]byte("anthares-ara-result-spool-v1:" + token))
	block, err := aes.NewCipher(key[:])
	if err != nil {
		return result, err
	}
	aead, err := cipher.NewGCM(block)
	if err != nil {
		return result, err
	}
	if len(data) < aead.NonceSize() {
		return result, errors.New("truncated encrypted result")
	}
	plain, err := aead.Open(nil, data[:aead.NonceSize()], data[aead.NonceSize():], []byte(id))
	if err != nil {
		return result, err
	}
	if err = json.Unmarshal(plain, &result); err != nil {
		return result, err
	}
	if result.ID != id {
		return result, errors.New("result identity mismatch")
	}
	return result, nil
}

func resultSpoolDir(cfg Config) string {
	key := sha256.Sum256([]byte(cfg.ControlURL + "|" + cfg.DeviceID))
	return filepath.Join(os.TempDir(), "anthares-ara-results", fmt.Sprintf("%x", key[:12]))
}

func replayEncryptedResults(cfg Config) error {
	dir := resultSpoolDir(cfg)
	entries, err := os.ReadDir(dir)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".pending") {
			continue
		}
		id := strings.TrimSuffix(entry.Name(), ".pending")
		path := filepath.Join(dir, entry.Name())
		result, err := loadEncryptedResult(path, cfg.DeviceToken, id)
		if err != nil {
			return fmt.Errorf("pending result %s: %w", id, err)
		}
		if err = postResultRetry(cfg, result); err != nil {
			return fmt.Errorf("replay result %s: %w", id, err)
		}
		if err = os.Remove(path); err != nil {
			return err
		}
	}
	return nil
}
