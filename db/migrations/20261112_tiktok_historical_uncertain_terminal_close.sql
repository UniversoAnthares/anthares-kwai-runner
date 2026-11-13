-- Approved administrative close-out: ten historical Oct 27 TikTok starts,
-- after independently authenticated Studio marker/title/public-profile checks.
-- This operation NEVER confirms remote delivery or authorizes reupload.
DO $anthares$
DECLARE
  v_open integer;
  v_closed integer;
  v_inserted integer;
  v_updated integer;
  v_audit_count integer;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtext('tiktok:universo.anthares'),hashtext('historical_uncertain_closeout_20261112'));

  CREATE TABLE IF NOT EXISTS public.cortes_tiktok_uncertain_resolution_audit (
    publication_id text NOT NULL,
    segment_id text PRIMARY KEY,
    previous_status text NOT NULL,
    resolution text NOT NULL,
    evidence_run_id bigint NOT NULL,
    evidence_url text NOT NULL,
    observed_inventory_count integer NOT NULL,
    inventory_complete boolean NOT NULL,
    remote_match_count integer NOT NULL,
    closed_at timestamptz NOT NULL DEFAULT now(),
    rationale text NOT NULL
  );

  SELECT count(*) FILTER (WHERE status='uncertain'),
         count(*) FILTER (WHERE status='closed_unverified')
    INTO v_open,v_closed
  FROM public.cortes_tiktok_publications
  WHERE source_id='A7BsgCe3-oo'
    AND publication_started_at >= timestamptz '2026-10-27 00:00:00+00'
    AND publication_started_at < timestamptz '2026-10-28 00:00:00+00';

  IF v_open=0 AND v_closed=10 THEN
    SELECT count(*) INTO v_audit_count
    FROM public.cortes_tiktok_uncertain_resolution_audit
    WHERE evidence_run_id=43329490208;
    IF v_audit_count<>10 THEN
      RAISE EXCEPTION 'HISTORIC_TIKTOK_CLOSEOUT_AUDIT_MISSING' USING ERRCODE='23514';
    END IF;
    RAISE NOTICE 'HISTORIC_TIKTOK_ALREADY_CLOSED_WITH_10_AUDIT_ROWS';
    RETURN;
  END IF;

  IF v_open<>10 OR v_closed<>0 THEN
    RAISE EXCEPTION 'HISTORIC_TIKTOK_SCOPE_UNEXPECTED open:% closed:%',v_open,v_closed USING ERRCODE='23514';
  END IF;

  IF (SELECT count(*) FROM public.cortes_tiktok_publications
      WHERE source_id='A7BsgCe3-oo' AND status='uncertain'
        AND publication_started_at >= timestamptz '2026-10-27 00:00:00+00'
        AND publication_started_at < timestamptz '2026-10-28 00:00:00+00'
        AND lease_until IS NULL AND remote_id IS NULL
        AND confirmed_at IS NULL AND last_error='after_started_requires_reconciliation')<>10 THEN
    RAISE EXCEPTION 'HISTORIC_TIKTOK_TERMINAL_FENCE_UNVERIFIED' USING ERRCODE='23514';
  END IF;

  ALTER TABLE public.cortes_tiktok_publications DROP CONSTRAINT cortes_tiktok_state;
  ALTER TABLE public.cortes_tiktok_publications
    ADD CONSTRAINT cortes_tiktok_state CHECK(status IN
      ('queued','leased','started','uncertain','confirmed','closed_unverified'));

  INSERT INTO public.cortes_tiktok_uncertain_resolution_audit
  (publication_id,segment_id,previous_status,resolution,evidence_run_id,evidence_url,
   observed_inventory_count,inventory_complete,remote_match_count,rationale)
  SELECT id,segment_id,status,'closed_unverified_no_reupload',
         43329490208,
         'https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43329490208',
         0,FALSE,0,
         'Authenticated TikTok Studio (marker and title queries) and owned public profile audited; 20 query pages, zero exact or title/date matches. Inventory completeness was not established, so remote absence cannot be proven. User-directed administrative closure; preserve immutable source/started-at and prohibit reupload.'
  FROM public.cortes_tiktok_publications
  WHERE source_id='A7BsgCe3-oo' AND status='uncertain'
    AND publication_started_at >= timestamptz '2026-10-27 00:00:00+00'
    AND publication_started_at < timestamptz '2026-10-28 00:00:00+00';
  GET DIAGNOSTICS v_inserted=ROW_COUNT;
  IF v_inserted<>10 THEN
    RAISE EXCEPTION 'HISTORIC_TIKTOK_AUDIT_INSERT_COUNT_%',v_inserted USING ERRCODE='23514';
  END IF;

  UPDATE public.cortes_tiktok_publications
    SET status='closed_unverified',
        last_error='closed_unverified_no_reupload:github_run_43329490208',
        updated_at=now()
  WHERE source_id='A7BsgCe3-oo' AND status='uncertain'
    AND publication_started_at >= timestamptz '2026-10-27 00:00:00+00'
    AND publication_started_at < timestamptz '2026-10-28 00:00:00+00'
    AND lease_until IS NULL AND remote_id IS NULL AND confirmed_at IS NULL;
  GET DIAGNOSTICS v_updated=ROW_COUNT;
  IF v_updated<>10 THEN
    RAISE EXCEPTION 'HISTORIC_TIKTOK_CLOSE_COUNT_%',v_updated USING ERRCODE='23514';
  END IF;
END
$anthares$;