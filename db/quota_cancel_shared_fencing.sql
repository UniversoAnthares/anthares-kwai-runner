-- Anthares quota cancellation shared lease / fencing ledger, v1.
-- Safe to apply on QA branch first; no grants to public and no external job dispatch.
BEGIN;
CREATE SCHEMA IF NOT EXISTS anthares_quota;
REVOKE ALL ON SCHEMA anthares_quota FROM PUBLIC;

CREATE TABLE IF NOT EXISTS anthares_quota.provider_health (
  provider text PRIMARY KEY,
  quota_scope text NOT NULL,
  eligible boolean NOT NULL DEFAULT false,
  independent_quota_verified boolean NOT NULL DEFAULT false,
  cancellation_capable boolean NOT NULL DEFAULT false,
  verified_at timestamptz,
  checked_at timestamptz NOT NULL DEFAULT now()
);
REVOKE ALL ON anthares_quota.provider_health FROM PUBLIC;

CREATE TABLE IF NOT EXISTS anthares_quota.attempts (
  attempt_id text PRIMARY KEY,
  task_id text NOT NULL,
  provider text NOT NULL,
  quota_scope text NOT NULL,
  state text NOT NULL CHECK (state IN (
    'RUNNING','CANCEL_REQUESTED','CANCEL_UNCONFIRMED',
    'RECONCILE_REQUIRED','CANCELLED_QUOTA','RESERVED',
    'FALLBACK_SUBMISSION_UNCERTAIN','SUCCEEDED','FAILED','CANCELLED_NO_INDEPENDENT_RESERVE')),
  fence bigint NOT NULL DEFAULT 1 CHECK (fence>0),
  lease_owner text,
  cancel_request_at timestamptz,
  terminal_confirmed_at timestamptz,
  external_status text,
  effect_proof text CHECK(effect_proof IN ('NOT_APPLIED','SAFE_NO_EFFECTS') OR effect_proof IS NULL),
  successor_attempt_id text UNIQUE,
  idempotency_key text UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (state <> 'CANCELLED_QUOTA' OR (terminal_confirmed_at IS NOT NULL AND effect_proof IS NOT NULL))
);
REVOKE ALL ON anthares_quota.attempts FROM PUBLIC;
CREATE UNIQUE INDEX IF NOT EXISTS anthares_quota_one_active_per_task
ON anthares_quota.attempts(task_id)
WHERE state IN ('RUNNING','CANCEL_REQUESTED','CANCEL_UNCONFIRMED',
                'RECONCILE_REQUIRED','RESERVED','FALLBACK_SUBMISSION_UNCERTAIN');
CREATE INDEX IF NOT EXISTS anthares_quota_pending_state_idx
ON anthares_quota.attempts(state,updated_at);

CREATE OR REPLACE FUNCTION anthares_quota.begin_cancellation(
 p_attempt_id text,p_expected_fence bigint,p_owner text
) RETURNS bigint LANGUAGE plpgsql SECURITY INVOKER AS $$
DECLARE v_fence bigint;
BEGIN
 UPDATE anthares_quota.attempts
    SET state='CANCEL_REQUESTED',fence=fence+1,
        cancel_request_at=clock_timestamp(),updated_at=clock_timestamp()
  WHERE attempt_id=p_attempt_id AND fence=p_expected_fence
    AND lease_owner=p_owner AND state='RUNNING'
  RETURNING fence INTO v_fence;
 RETURN v_fence;
END $$;

CREATE OR REPLACE FUNCTION anthares_quota.confirm_cancellation(
 p_attempt_id text,p_expected_fence bigint,p_terminal_status text,p_effect_proof text
) RETURNS boolean LANGUAGE plpgsql SECURITY INVOKER AS $$
DECLARE v_id text;
BEGIN
 IF p_terminal_status NOT IN ('CANCELED','CANCELLED','FAILED','TERMINATED','EXPIRED')
    OR p_effect_proof NOT IN ('NOT_APPLIED','SAFE_NO_EFFECTS') THEN
    RETURN false;
 END IF;
 UPDATE anthares_quota.attempts
   SET state='CANCELLED_QUOTA',lease_owner=NULL,external_status=p_terminal_status,
       effect_proof=p_effect_proof,terminal_confirmed_at=clock_timestamp(),
       updated_at=clock_timestamp()
 WHERE attempt_id=p_attempt_id AND fence=p_expected_fence
   AND state='CANCEL_REQUESTED'
 RETURNING attempt_id INTO v_id;
 RETURN v_id IS NOT NULL;
END $$;

CREATE OR REPLACE FUNCTION anthares_quota.reserve_successor(
 p_previous text,p_new_attempt text,p_provider text,p_idempotency text
) RETURNS boolean LANGUAGE plpgsql SECURITY INVOKER AS $$
DECLARE old_attempt anthares_quota.attempts%ROWTYPE;
DECLARE reserve anthares_quota.provider_health%ROWTYPE;
DECLARE inserted text;
BEGIN
 IF p_previous IS NULL OR p_new_attempt IS NULL OR p_idempotency IS NULL THEN
    RETURN false;
 END IF;
 SELECT * INTO old_attempt FROM anthares_quota.attempts
    WHERE attempt_id=p_previous FOR UPDATE;
 IF NOT FOUND OR old_attempt.state <> 'CANCELLED_QUOTA'
    OR old_attempt.effect_proof NOT IN ('NOT_APPLIED','SAFE_NO_EFFECTS')
    OR old_attempt.successor_attempt_id IS NOT NULL THEN
   RETURN false;
 END IF;
 SELECT * INTO reserve FROM anthares_quota.provider_health
    WHERE provider=p_provider AND eligible AND cancellation_capable
      AND independent_quota_verified AND verified_at > now() - interval '30 minutes';
 IF NOT FOUND OR reserve.quota_scope=old_attempt.quota_scope THEN
    RETURN false;
 END IF;
 INSERT INTO anthares_quota.attempts
 (attempt_id,task_id,provider,quota_scope,state,fence,idempotency_key)
 VALUES (p_new_attempt,old_attempt.task_id,reserve.provider,reserve.quota_scope,
         'RESERVED',1,p_idempotency)
 ON CONFLICT DO NOTHING
 RETURNING attempt_id INTO inserted;
 IF inserted IS NULL THEN RETURN false; END IF;
 UPDATE anthares_quota.attempts SET successor_attempt_id=inserted,
 updated_at=clock_timestamp() WHERE attempt_id=p_previous;
 RETURN true;
END $$;

REVOKE ALL ON FUNCTION anthares_quota.begin_cancellation(text,bigint,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION anthares_quota.confirm_cancellation(text,bigint,text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION anthares_quota.reserve_successor(text,text,text,text) FROM PUBLIC;
COMMIT;
