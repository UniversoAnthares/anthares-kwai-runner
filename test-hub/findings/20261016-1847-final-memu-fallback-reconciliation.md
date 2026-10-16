# Final MEmu fallback reconciliation

- SYSTEM remains the canonical authority and tries MEmu headless + ADB 5037 first.
- Real test proved persistent ADB failure when the VM remained in Session 0.
- Recovery now powers off only MEmu after SYSTEM-path exhaustion, then invokes the disabled-by-default interactive launcher + ADB 5038 fallback.
- Real takeover proof: MEmuHeadless restarted in Session 1; 5038 reported device; sys.boot_completed=1; com.kwai.video installed.
- After interactive restart, ADB 5037 became healthy again, so runtime hands transport back to SYSTEM and stops 5038.
- Fallback tasks are disabled again after recovery.
- Recovery mutex rotated to Global\AntharesMEmuRecoveryAuthorityV2 to retire the stale orphaned mutex observed during concurrent-agent testing.
- Windows reboot acceptance remains intentionally pending owner action.
