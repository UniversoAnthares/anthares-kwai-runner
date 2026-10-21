-- CORTES TikTok: production-enforced limit independent of the Vercel
-- deployment quota and of GitHub/browser worker availability.
-- Safe to reapply. One confirmed or uncertain STARTED reserves one slot,
-- per TikTok account and America/Campo_Grande calendar day.
-- The common budget table was created by
-- 20261021_cortes_daily_publication_limit_100.sql.
-- Never delete uncertain publication rows to reclaim budget.
CREATE OR REPLACE FUNCTION public.cortes_tiktok_reserve_daily_start_v1()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, public
AS $guard$
DECLARE
  v_day date;
  v_reserved integer;
BEGIN
  IF NEW.status = 'started'
     AND OLD.status = 'leased'
     AND OLD.publication_started_at IS NULL
     AND NEW.publication_started_at IS NOT NULL THEN
    v_day := (NEW.publication_started_at AT TIME ZONE 'America/Campo_Grande')::date;
    INSERT INTO public.cortes_daily_publication_budget
      (target_key, local_day, reserved, updated_at)
    VALUES ('tiktok:universo.anthares', v_day, 1, now())
    ON CONFLICT (target_key, local_day) DO UPDATE
      SET reserved = public.cortes_daily_publication_budget.reserved + 1,
          updated_at = now()
      WHERE public.cortes_daily_publication_budget.reserved < 100
    RETURNING reserved INTO v_reserved;
    IF v_reserved IS NULL THEN
      RAISE EXCEPTION 'CORTES_TIKTOK_DAILY_START_LIMIT_100'
        USING ERRCODE = '23514';
    END IF;
  END IF;
  RETURN NEW;
END;
$guard$;

-- Backfill only (no row is removed or reset).
INSERT INTO public.cortes_daily_publication_budget
  (target_key,local_day,reserved,updated_at)
SELECT 'tiktok:universo.anthares',
  (publication_started_at AT TIME ZONE 'America/Campo_Grande')::date,
  LEAST(COUNT(*),100)::integer,now()
FROM public.cortes_tiktok_publications
WHERE publication_started_at IS NOT NULL
GROUP BY (publication_started_at AT TIME ZONE 'America/Campo_Grande')::date
ON CONFLICT (target_key,local_day) DO UPDATE
SET reserved=GREATEST(public.cortes_daily_publication_budget.reserved,EXCLUDED.reserved),
    updated_at=now();

DO $once$
BEGIN
  IF NOT EXISTS (
      SELECT 1 FROM pg_trigger
      WHERE tgrelid='public.cortes_tiktok_publications'::regclass
        AND tgname='cortes_tiktok_daily_start_guard_v1'
        AND NOT tgisinternal) THEN
    CREATE TRIGGER cortes_tiktok_daily_start_guard_v1
      BEFORE UPDATE OF status,publication_started_at
      ON public.cortes_tiktok_publications
      FOR EACH ROW
      EXECUTE FUNCTION public.cortes_tiktok_reserve_daily_start_v1();
  END IF;
END
$once$;
