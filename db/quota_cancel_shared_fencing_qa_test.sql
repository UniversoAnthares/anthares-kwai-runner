-- Isolated functional test of quota cancellation PostgreSQL ledger.
-- Single DO statement: atomic rollback on failure; all QA rows deleted on success.
DO $anthares$
DECLARE
  task text := 'anthares-qa-cancel-test-20261027';
  token bigint;
  ok boolean;
BEGIN
 INSERT INTO anthares_quota.provider_health
  (provider,quota_scope,eligible,independent_quota_verified,cancellation_capable,verified_at)
 VALUES
  ('qa-quota-source','qa-scope-A',true,true,true,now()),
  ('qa-quota-standby','qa-scope-B',true,true,true,now())
 ON CONFLICT(provider) DO UPDATE SET verified_at=now(),checked_at=now();
 INSERT INTO anthares_quota.attempts
  (attempt_id,task_id,provider,quota_scope,state,lease_owner)
 VALUES(task||'-1',task,'qa-quota-source','qa-scope-A','RUNNING','qa-owner');
 token:=anthares_quota.begin_cancellation(task||'-1',1,'qa-owner');
 IF token IS DISTINCT FROM 2 THEN RAISE EXCEPTION 'FENCE_INCREMENT_FAILED'; END IF;
 ok:=anthares_quota.confirm_cancellation(task||'-1',1,'CANCELLED','NOT_APPLIED');
 IF ok THEN RAISE EXCEPTION 'STALE_FENCE_ACCEPTED'; END IF;
 ok:=anthares_quota.confirm_cancellation(task||'-1',token,'RUNNING','NOT_APPLIED');
 IF ok THEN RAISE EXCEPTION 'NONTERMINAL_STATUS_ACCEPTED'; END IF;
 ok:=anthares_quota.confirm_cancellation(task||'-1',token,'CANCELLED','NOT_APPLIED');
 IF NOT ok THEN RAISE EXCEPTION 'TERMINAL_CONFIRMATION_FAILED'; END IF;
 ok:=anthares_quota.reserve_successor(task||'-1',task||'-2','qa-quota-source',task||'-same-quota');
 IF ok THEN RAISE EXCEPTION 'SAME_QUOTA_RESERVE_ACCEPTED'; END IF;
 ok:=anthares_quota.reserve_successor(task||'-1',task||'-2','qa-quota-standby',task||'-idempotent');
 IF NOT ok THEN RAISE EXCEPTION 'VALID_RESERVE_FAILED'; END IF;
 ok:=anthares_quota.reserve_successor(task||'-1',task||'-3','qa-quota-standby',task||'-duplicated');
 IF ok THEN RAISE EXCEPTION 'DUPLICATE_RESERVE_ACCEPTED'; END IF;
 IF (SELECT count(*) FROM anthares_quota.attempts WHERE task_id=task AND state='RESERVED') <> 1
 THEN RAISE EXCEPTION 'SINGLE_ACTIVE_WRITER_FAILED'; END IF;
 DELETE FROM anthares_quota.attempts WHERE task_id=task;
 DELETE FROM anthares_quota.provider_health WHERE provider IN ('qa-quota-source','qa-quota-standby');
END $anthares$;
