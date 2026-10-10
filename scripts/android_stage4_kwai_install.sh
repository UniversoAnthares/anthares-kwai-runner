#!/usr/bin/env bash
set -euo pipefail
mkdir -p /tmp/anthares-stage4
curl -fL --retry 3 --connect-timeout 15 --max-time 180 -o /tmp/anthares-stage4/kwai-vault.zip 'https://github.com/UniversoAnthares/anthares-kwai-runner/releases/download/kwai-package-vault/kwai-vault.zip'
echo '96650454576a2cf5cc5e63d90011f0b60a03d2702605756f40cc934cd6ae5543  /tmp/anthares-stage4/kwai-vault.zip' | sha256sum -c -
python3 - <<'PY'
import zipfile
from pathlib import Path
p=Path('/tmp/anthares-stage4/kwai-vault.zip')
dest=Path('kwai-vault')
dest.mkdir(exist_ok=True)
with zipfile.ZipFile(p) as z:
    for info in z.infolist():
        name=Path(info.filename)
        if name.is_absolute() or '..' in name.parts:
            raise ValueError('unsafe archive path')
        if not info.is_dir() and info.filename.lower().endswith('.apk'):
            out=dest/name.name
            if out.exists(): raise ValueError('duplicate APK basename')
            out.write_bytes(z.read(info))
print('APK_COUNT',len(list(dest.glob('*.apk'))))
PY
bash kwai_vault_install.sh | tee /tmp/anthares-stage4/install.txt
adb shell pm path com.kwai.video | tee /tmp/anthares-stage4/package.txt
adb shell dumpsys activity activities > /tmp/anthares-stage4/activity.txt
adb shell screencap -p /sdcard/anthares-kwai-stage4.png
adb pull /sdcard/anthares-kwai-stage4.png /tmp/anthares-stage4/screenshot.png
test -s /tmp/anthares-stage4/screenshot.png
echo KWAI_STAGE4_INSTALL_AND_LAUNCH_OK
