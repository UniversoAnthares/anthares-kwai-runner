# ARA portable controller (no Cloudflare / no Render)

Provider-neutral HTTP controller using the existing Floot/PostgreSQL schema. This is **source code only**, not a running backup.

Requires `DATABASE_URL`, `ARA_CONTROLLER_ID` (unique owner identifier in ara_fence_leases), and optional `PORT`. Set `DATABASE_SSL=disable` only for local tests.

The service **does not acquire or promote itself**. Device operations are rejected with HTTP 423 until the shared fence is assigned to this controller. This is intentional: a second owner must never steal a live lease.

Compatible routes: /healthz, /v1/device/auth-check, /v1/device/heartbeat, /v1/device/jobs/next, /v1/device/jobs/:id/result.

Not ready for production promotion: controller identity must be authenticated independently from device bearer, old-controller queue handover must be completed, and agent-side epoch verification must be proven. Jobs with unknown outcomes must never be automatically retried.

This source can be deployed to a **non-Render, non-Cloudflare** host with a long-running Node 20+ process and PostgreSQL network connectivity, after the security gates pass. No hosting provider has been provisioned or selected.
