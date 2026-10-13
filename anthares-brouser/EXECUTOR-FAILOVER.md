# Alternative executors for Anthares-browser

Priority and failover are **control-plane choices**, not a claim that all providers are provisioned.

1. GitLab CI (independent GitLab-hosted runners). Repository mirror: https://gitlab.com/universo-anthares-group/anthares-kwai-runner ; verify source SHA matches GitHub before any run. GitLab project default branch is duo-main and is not automatically the same commit as GitHub main.
2. Render (remote container runtime). Existing Render services are not dedicated browser CI runners. Only use a separately authenticated test endpoint with explicit capacity and limits. Do not reuse public production endpoints as arbitrary command execution.
3. Anthares infrastructure (independent of Render). PENDING: deploy a private job worker with persistent queue, auth, leases and telemetry, then verify remotely with PC off.

Do not automatically fail over on test failures: fail over only on infrastructure failure (runner unavailable, scheduling timeout, provider outage). Keep a common SHA and test manifest across all three providers. Never silently fall back to GitHub Actions or to the user's computer.

To claim operational failover: prove each provider executes the same test manifest, reports an exit status, retains redacted logs and is accessible without GitHub-hosted runners.
