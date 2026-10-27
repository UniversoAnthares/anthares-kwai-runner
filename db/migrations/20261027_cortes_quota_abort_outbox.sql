-- CORTES-QUOTA-01: cancellation-first durable ledger, additive migration.
-- No publication is performed by triggers or schema installation.
-- Only a dedicated, authorized controller may claim event leases.
CREATE TABLE IF NOT EXISTS public.cortes_quota_abort_events (
  event_id text PRIMARY KEY,
  task_id text,
  source_run_id text,
  source_provider text,
  executor_quota_pool text,
  platform_quota_pool text,
  target_key text,
  idempotency_key text,
  quota_scope text,
  failure_reason text,
  state text NOT NULL DEFAULT 'NEW',
  lease_token uuid,
  lease_generation bigint NOT NULL DEFAULT 0,
  lease_until timestamptz,
  destination_provider text,
  revision bigint NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT cortes_quota_abort_state_ck CHECK (state IN (
    'NEW', 'CANCEL_REQUESTED', 'CANCELLED_QUOTA',
    'CANCEL_UNCONFIRMED', 'RECEIPT_UNCERTAIN',
    'COMPLETED_ORIGINAL', 'HANDOFF_QUEUED', 'BLOCKED_NO_CAPACITY')),
  CONSTRAINT cortes_quota_abort_scope_ck CHECK (
    quota_scope IS NULL OR quota_scope IN
    ('executor', 'credential', 'organization', 'platform'))
);
CREATE UNIQUE INDEX IF NOT EXISTS cortes_quota_abort_attempt_identity_uq
 ON public.cortes_quota_abort_events(task_id, target_key, source_run_id)
 WHERE task_id IS NOT NULL AND target_key IS NOT NULL AND source_run_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS cortes_quota_abort_lease_idx
 ON public.cortes_quota_abort_events(lease_until)
 WHERE state NOT IN ('COMPLETED_ORIGINAL', 'HANDOFF_QUEUED');

CREATE TABLE IF NOT EXISTS public.cortes_quota_handoff_outbox (
  event_id text PRIMARY KEY REFERENCES public.cortes_quota_abort_events(event_id),
  task_id text NOT NULL,
  target_key text NOT NULL,
  idempotency_key text NOT NULL,
  destination_provider text NOT NULL,
  state text NOT NULL DEFAULT 'PENDING',
  claim_token uuid,
  claimed_until timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT cortes_quota_outbox_state_ck CHECK (state IN (
    'PENDING', 'CLAIMED', 'CONFIRMED', 'RECONCILIATION_REQUIRED')),
  CONSTRAINT cortes_quota_outbox_dedupe_uq UNIQUE(target_key, idempotency_key)
);
CREATE INDEX IF NOT EXISTS cortes_quota_handoff_pending_idx
 ON public.cortes_quota_handoff_outbox(created_at)
 WHERE state='PENDING';
-- Fail closed if transport receipt is uncertain. A separate authorized
-- consumer must reconcile before enqueue. Keep the platform/account quota.
