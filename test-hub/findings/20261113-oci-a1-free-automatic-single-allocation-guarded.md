# OCI A1 Always Free — auto allocation authorized, guarded, pending capacity
STATUS: PARTIAL
AREA: android
DATE: 2026-11-13
RUN: no live Compute launch; isolated unit tests
JOBS: ARA 2b49e56ef77043239b5ef1aeed3b392f; ARA b3ac80d20f372ea252c35f2f3bdc25e6
COMMIT: branch feat/oci-a1-guarded-free-automatic-launch-20261113
SUPERSEDES: test-hub/findings/20261113-oci-a1-subnet-ssh-pinned-live-readonly-preflight.md

## BASELINE_PROVEN
Monitor OCI hosted GitHub run #43462060914 PASS with 27 tests and logged `ANTHARES_A1_CAPACITY=OUT_OF_HOST_CAPACITY`, `ANTHARES_A1_NETWORK_MODE=LOCKED_PUBLIC`, `ANTHARES_A1_PROVISION_PREFLIGHT=READY_SSH_SUBNET_NETWORK`. Approved SSH public key pinned (no private key in GitHub); user authorized continuing with cloud Android Always Free.

Authenticated OCI API real read-only preflight: exactly one active Android subnet with locked SSH ingress; 3 Ubuntu 24.04 ARM64 images eligible; zero active VM A1, zero GiB of allocated boot/block volumes; 50 GiB Always Free boot fits 200 GiB pool; current administrator public IP matches subnet firewall /32 (no IP returned to this finding).

## CHANGE
- Workflow OCI watcher progresses from `AUTO_PROVISION=0` to `AUTO_PROVISION=1` with guard `ALWAYS_FREE_SINGLE_A1`, retaining 4h cron and single concurrency. The watcher's Python guards still require A1 `AVAILABLE`, shape 1 OCPU/6 GiB, 50 GiB boot, image Ubuntu ARM64 from approved family, approved subnet and key, existing A1 count zero, sum of volumes +50 <=200, and a stable OPC retry token. No paid shapes, alternative regions, public ADB, credential exfiltration or Kwai publishing.
- `occupied_block_volume_gib` rejects active boot/block volume of unknown, invalid or zero size; previously size `None` was counted as 0. This closes a free-quota overrun risk.

## UNIT_TESTS
- New tests execute full `main()` with mock OCI report `AVAILABLE`: 1 permitted `launch_instance` with shape A1 1 OCPU/6 GiB, 50 GiB boot, source VNIC public IP protected, ssh_key metadata, stable OPC retry token. Tests also reject >200 GiB, missing launch guard and unknown-size volumes.
- Previous 27 tests PASS; new set of 10 tests including these four scenarios PASS, 0 failures, 0 errors (ARA `2b49e56ef77043239b5ef1aeed3b392f`). Test errors encountered while exercising code without a checkout were corrected by mocking cloud-init contents, rather than writing source files on Windows.

## LIMITS
- `AVAILABLE` in mocks is only a synthetic success signal; last real OCI capacity still `OUT_OF_HOST_CAPACITY`, so no VM has been created.
- After merging, verify GitHub Actions PASS and capacity still `OUT_OF_HOST_CAPACITY`; if an actual instance is allocated, inspect state, cloud-init, binder and Docker before adding Android apps.
- No Kwai credentials, MacroDroid tokens or Neon publishing permissions are present in first-boot. Further work requires post-boot setup and authorization.
- Cost-free eligibility derived from Oracle published Always Free A1 (2 OCPUs/12 GiB equivalent monthly) and 200 GiB storage allowances. Account billing alert remains non-blocking; avoid any paid extras.
