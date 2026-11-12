-- CORTES publication hard window 06:00 <= time < 23:00 America/Campo_Grande.
-- Idempotent additive guard: never deletes rows, budget reservations or evidence.
-- This trigger is independent of Neon Functions, Vercel, GitHub and Cloudflare.
-- Both TikTok accounts are independently fenced by table, local date and OIDC leases.
CREATE OR REPLACE FUNCTION public.cortes_tiktok_proportional_start_guard_20261112()
RETURNS trigger
LANGUAGE plpgsql
SET search_path TO pg_catalog, public
AS $guard$
DECLARE
 v_now timestamptz := clock_timestamp();
 v_local_time time;
 v_day date;
 v_target text;
 v_used integer;
 v_queued integer;
 v_leased integer;
 v_remaining integer;
 v_last_started timestamptz;
 v_last_confirmed timestamptz;
 v_anchor timestamptz;
 v_last_slot timestamptz;
 v_due timestamptz;
BEGIN
 IF NOT (
   TG_OP = 'UPDATE'
   AND NEW.status = 'started'
   AND OLD.status = 'leased'
   AND OLD.publication_started_at IS NULL
   AND NEW.publication_started_at IS NOT NULL
 ) THEN
   RETURN NEW;
 END IF;
 IF TG_TABLE_NAME='cortes_tiktok_publications' THEN
   v_target := 'tiktok:universo.anthares';
 ELSIF TG_TABLE_NAME='cortes_tiktok_lucasrosalem4_publications' THEN
   v_target := 'tiktok:lucasrosalem4';
 ELSE
   RAISE EXCEPTION 'CORTES_PACING_UNKNOWN_TIKTOK_TABLE' USING ERRCODE='23514';
 END IF;
 v_local_time := (v_now AT TIME ZONE 'America/Campo_Grande')::time;
 v_day := (v_now AT TIME ZONE 'America/Campo_Grande')::date;
 IF v_local_time < time '06:00:00' OR v_local_time >= time '23:00:00' THEN
   RAISE EXCEPTION 'CORTES_TIKTOK_HARD_WINDOW_06_23' USING ERRCODE='23514';
 END IF;
 -- Additional per-account/day lock; budget triggers remain unchanged.
 PERFORM pg_advisory_xact_lock(hashtext('CORTES_TIKTOK_06_23'),hashtext(v_target||':'||v_day::text));
 EXECUTE format(
   'SELECT '||
   'count(*) FILTER (WHERE publication_started_at IS NOT NULL AND '||
   '(publication_started_at AT TIME ZONE ''America/Campo_Grande'')::date=$1)::int,'||
   'count(*) FILTER (WHERE status=''queued'' AND '||
   '(retry_not_before IS NULL OR retry_not_before<=$2))::int,'||
   'count(*) FILTER (WHERE status=''leased'' AND lease_until>$2)::int,'||
   'max(publication_started_at) FILTER (WHERE publication_started_at IS NOT NULL AND '||
   '(publication_started_at AT TIME ZONE ''America/Campo_Grande'')::date=$1),'||
   'max(confirmed_at) FILTER (WHERE status=''confirmed'' AND '||
   '(confirmed_at AT TIME ZONE ''America/Campo_Grande'')::date=$1)'||
   ' FROM public.%I',TG_TABLE_NAME)
 INTO v_used,v_queued,v_leased,v_last_started,v_last_confirmed
 USING v_day,v_now;
 v_remaining := LEAST(v_queued+v_leased,GREATEST(0,100-v_used));
 IF v_remaining < 1 THEN
   RAISE EXCEPTION 'CORTES_TIKTOK_DAILY_CAPACITY_EXHAUSTED' USING ERRCODE='23514';
 END IF;
 v_anchor := GREATEST(v_last_confirmed,v_last_started);
 IF v_anchor IS NULL THEN
   -- First real start at first eligible wake-up at or after 06:00.
   RETURN NEW;
 END IF;
 v_last_slot := ((v_day + time '22:59:00') AT TIME ZONE 'America/Campo_Grande');
 IF v_anchor >= v_last_slot THEN
   RAISE EXCEPTION 'CORTES_TIKTOK_LAST_SLOT_ALREADY_REACHED' USING ERRCODE='23514';
 END IF;
 v_due := v_anchor+(v_last_slot-v_anchor)/v_remaining;
 IF v_now < v_due THEN
   RAISE EXCEPTION 'CORTES_TIKTOK_PROPORTIONAL_EARLY_START next_due=%',v_due
     USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END;
$guard$;

DO $once$
BEGIN
 IF NOT EXISTS (
   SELECT 1 FROM pg_trigger
   WHERE tgrelid='public.cortes_tiktok_publications'::regclass
     AND tgname='cortes_tiktok_hard_window_06_23_v1'
     AND NOT tgisinternal
 ) THEN
   CREATE TRIGGER cortes_tiktok_hard_window_06_23_v1
   BEFORE UPDATE OF status,publication_started_at
   ON public.cortes_tiktok_publications
   FOR EACH ROW
   EXECUTE FUNCTION public.cortes_tiktok_proportional_start_guard_20261112();
 END IF;
 IF NOT EXISTS (
   SELECT 1 FROM pg_trigger
   WHERE tgrelid='public.cortes_tiktok_lucasrosalem4_publications'::regclass
     AND tgname='cortes_tiktok4_hard_window_06_23_v1'
     AND NOT tgisinternal
 ) THEN
   CREATE TRIGGER cortes_tiktok4_hard_window_06_23_v1
   BEFORE UPDATE OF status,publication_started_at
   ON public.cortes_tiktok_lucasrosalem4_publications
   FOR EACH ROW
   EXECUTE FUNCTION public.cortes_tiktok_proportional_start_guard_20261112();
 END IF;
END;
$once$;
