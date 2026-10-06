# Lease: Kwai resource-loading causal closure 30-way
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
LEASE_AREA: kwai-login
LEASE_EXPIRES: 2026-10-06T12:08:00Z
BASELINE_PROVEN: 30-way real-auth run 37455990989 proved vault install + KWAI_LAUNCHED on executed replicas; failures converge on V2_LOGIN_NODES=0/AUTOLOGIN_RC=3. Current state driver now identifies resource downloading as a blocking state.
FAILED_AVOIDED: do not repeat direct autologin before FSM_MAIN_REACHED; do not interpret cancelled replicas as auth failures; do not retry bare ikwai://login router.
SUCCESS_SIGNAL: at least one replica emits RESOURCE_LOADING_CLEARED then FSM_MAIN_REACHED and reaches the known Phone auth surface; real credential use remains serialized.
FAILURE_SIGNAL: 30 valid replicas reach RESOURCE_LOADING_TIMEOUT without MAIN, establishing that GitHub disposable Android cannot hydrate this resource module under the current acquisition path.
TEST_VALIDITY: replica counts only after KWAI_LAUNCHED and explicit RESOURCE_LOADING state; emulator/ADB/bootstrap failures are INVALID harness results.
