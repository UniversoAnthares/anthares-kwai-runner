# Kwai Android runtime — installation proven; AccessibilityService is current blocker

STATUS: PROVEN
DATE: 2026-10-06
AREA: kwai-login
RUNS: 37415036743; 37414464624; 37415273062

## Proven
- Run 37415036743 completed SUCCESS.
- Emulator booted with KVM and explicit AVD paths.
- The validated vault split APK set installed successfully via adb install-multiple.
- com.kwai.video was present after installation.
- Runtime 37414464624 independently reached TEST_VALIDITY=APPS_INSTALLED.

## Current blocker
- Agent APK installs and declares us.anthares.agent/.AntharesAccessibilityService correctly with BIND_ACCESSIBILITY_SERVICE.
- On run 37415273062, Android reported the service in the resolver table, but enabled_accessibility_services returned null and dumpsys accessibility showed Enabled services:{} / Bound services:{}.
- Therefore the failure is specifically activation/binding of the declared AccessibilityService, after successful Kwai+agent installation.

## Next probe
- Explicit --user 0 secure settings.
- Open ACCESSIBILITY_SETTINGS before write.
- Initialize agent process after write.
- Verify setting and dumpsys before proceeding to MAIN.

Do not regress the proven direct split APK installation or AVD/KVM fixes.
