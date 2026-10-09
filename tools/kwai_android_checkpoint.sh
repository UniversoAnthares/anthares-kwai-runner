#!/usr/bin/env bash
# Encrypted, complete Android AVD checkpoint transport. Requires private storage supplied by caller.
set -euo pipefail
umask 077
MODE="${1:?usage: checkpoint.sh save|restore}"
AVD_DIR="${AVD_DIR:-$HOME/.android/avd}"
AVD_NAME="${AVD_NAME:-kwai-speed}"
AVD_PATH="$AVD_DIR/$AVD_NAME.avd"
INI_PATH="$AVD_DIR/$AVD_NAME.ini"
: "${KWAI_CHECKPOINT_KEY:?Set a secret encryption passphrase in a protected runner secret}"
: "${KWAI_PRIVATE_CHECKPOINT_URL:?Set private read/write checkpoint URL}"
: "${KWAI_PRIVATE_CHECKPOINT_TOKEN:?Set private storage credential}"
[[ "$KWAI_PRIVATE_CHECKPOINT_URL" == https://* ]] || { echo 'HTTPS_REQUIRED'; exit 3; }
command -v openssl >/dev/null
command -v curl >/dev/null
command -v tar >/dev/null
if [[ "$MODE" == save ]]; then
  # Consistency: stop emulator, and require all qemu processes to have exited.
  adb emu kill >/dev/null 2>&1 || true
  for i in $(seq 1 30); do
    if ! pgrep -f '[q]emu-system.*kwai-speed' >/dev/null; then break; fi
    sleep 1
  done
  if pgrep -f '[q]emu-system.*kwai-speed' >/dev/null; then echo 'EMULATOR_STILL_RUNNING'; exit 4; fi
  test -d "$AVD_PATH" && test -f "$INI_PATH"
  tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
  tar -C "$AVD_DIR" -czf "$tmp/avd.tgz" "$AVD_NAME.avd" "$AVD_NAME.ini"
  openssl enc -aes-256-cbc -pbkdf2 -iter 250000 -salt -pass env:KWAI_CHECKPOINT_KEY -in "$tmp/avd.tgz" -out "$tmp/avd.enc"
  sha256sum "$tmp/avd.enc" | awk '{print $1}' > "$tmp/avd.sha256"
  curl --fail --silent --show-error --retry 3 -X PUT -H "Authorization: Bearer $KWAI_PRIVATE_CHECKPOINT_TOKEN" --data-binary @"$tmp/avd.enc" "$KWAI_PRIVATE_CHECKPOINT_URL"
  echo "CHECKPOINT_ENCRYPTED_UPLOAD_OK sha256=$(cat "$tmp/avd.sha256")"
elif [[ "$MODE" == restore ]]; then
  tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
  curl --fail --silent --show-error --retry 3 -H "Authorization: Bearer $KWAI_PRIVATE_CHECKPOINT_TOKEN" -o "$tmp/avd.enc" "$KWAI_PRIVATE_CHECKPOINT_URL"
  test -s "$tmp/avd.enc"
  openssl enc -d -aes-256-cbc -pbkdf2 -iter 250000 -pass env:KWAI_CHECKPOINT_KEY -in "$tmp/avd.enc" -out "$tmp/avd.tgz"
  mkdir -p "$AVD_DIR"
  python3 - "$tmp/avd.tgz" "$AVD_NAME" <<'PY'
import sys, tarfile, pathlib
with tarfile.open(sys.argv[1], "r:gz") as archive:
    avd = sys.argv[2]
    for member in archive.getmembers():
        p = pathlib.PurePosixPath(member.name)
        if p.is_absolute() or ".." in p.parts or not (member.name == avd + ".ini" or (p.parts and p.parts[0] == avd + ".avd")) or member.issym() or member.islnk() or member.isdev():
            raise SystemExit("UNSAFE_AVD_ARCHIVE")
PY
  if [[ -e "$AVD_PATH" || -e "$INI_PATH" ]]; then echo 'REFUSE_OVERWRITE_EXISTING_AVD'; exit 5; fi
  tar -C "$AVD_DIR" -xzf "$tmp/avd.tgz" --no-same-owner
  echo 'CHECKPOINT_DECRYPTED_RESTORE_OK; AUTH_IDENTITY_NOT_VERIFIED'
else
  echo 'UNKNOWN_MODE'; exit 2
fi
