# ARA quota-independent recovery
STATUS: RUNNING
AREA: cloudflare / ara-oauth / private-queue
DATE: 2026-11-26
BASE_HEAD: 66fa7424ec2132da6bee73fc96d0de61ffc149db
SOURCE_BLOB: 89c7e65fd84daced97bfcacce22cfbc4b25095b5
PEER: GitLab main index blob 56e84f954b741b44cfdfc4c6e18aa6d9d8766776 differs; no peer write or mirror requested.
GOVERNANCE: rules 821bdcb8d8479b0c28371a6f058b4b32d86a3fa1; index a4ae3b20fd2a07e97d75825acfe8f2a77beb0caf; master 26fb0b564d02bd4ca7067f85547f973f900522ce
BASELINE_PROVEN: Neon HTTP 402, standby HTTP 503; both legacy Cloudflare reserves authenticated but disconnected. Private queue issue #330 returned matching successful agent_health receipt; closed with result. One canonical agent remains active.
FAILED_AVOIDED: Do not repeat Neon quota calls; do not move existing token replay claims to another store, bypass OAuth, or repeat an uncertain command. No restart, production deployment or extra cost.
SUCCESS_SIGNAL: isolated tests demonstrate new recovery token signature domain, atomic one-time claim, fail-closed unavailable replay store and no anonymous queue submissions; existing tests pass.
FAILURE_SIGNAL: replay accepted, legacy token accepted in recovery epoch, public health queues jobs, or duplicate writes.
TEST_VALIDITY: branch-only code and synthetic offline regressions; production promotion requires reviewed change, owner OAuth reconnection and authenticated canary.
LEASE_SCOPE: isolated branch fix/ara-quota-independent-recovery-20261126 only. No shared-main or GitLab mutation.
