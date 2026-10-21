-- 2026-10-21 CORTES P0. Apply after verifying Neon branch tests.
-- Global cross-consumer, cross-account platform cap: never begin >100/day/platform.
-- Preserves existing per-target reservations and independently fences TikTok.
CREATE OR REPLACE FUNCTION public.cortes_platform_daily_cap_100()
RETURNS trigger LANGUAGE plpgsql
SET search_path TO 'pg_catalog','public'
AS $body$
DECLARE v_platform text; v_day date; v_reserved integer; v_count boolean;
BEGIN
  IF TG_OP = 'INSERT' THEN
    v_count := (NEW.status IN ('started','confirmed') OR NEW.publication_started_at IS NOT NULL);
  ELSE
    v_count := (OLD.status IS DISTINCT FROM 'confirmed')
       AND ((OLD.publication_started_at IS NULL AND NEW.publication_started_at IS NOT NULL)
       OR (OLD.publication_started_at IS NULL AND OLD.status IS DISTINCT FROM NEW.status
           AND NEW.status IN ('started','confirmed')));
  END IF;
  IF NOT v_count THEN RETURN NEW; END IF;
  IF TG_TABLE_NAME='cortes_tiktok_publications' THEN
    v_platform:='tiktok';
  ELSE
    v_platform:=lower(split_part(NEW.target_key,':',1));
  END IF;
  IF v_platform !~ '^[a-z][a-z0-9_-]{0,30}$' THEN
    RAISE EXCEPTION 'CORTES_PLATFORM_TARGET_INVALID' USING ERRCODE='23514';
  END IF;
  IF NEW.status='started' AND NEW.publication_started_at IS NULL THEN
    NEW.publication_started_at:=now();
  END IF;
  v_day:=(COALESCE(NEW.publication_started_at,now()) AT TIME ZONE 'America/Campo_Grande')::date;
  INSERT INTO public.cortes_daily_publication_budget(target_key,local_day,reserved,updated_at)
  VALUES ('platform:'||v_platform,v_day,1,now())
  ON CONFLICT (target_key,local_day) DO UPDATE
    SET reserved=public.cortes_daily_publication_budget.reserved+1,updated_at=now()
    WHERE public.cortes_daily_publication_budget.reserved<100
  RETURNING reserved INTO v_reserved;
  IF v_reserved IS NULL THEN
    RAISE EXCEPTION 'CORTES_PLATFORM_DAILY_LIMIT_100' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END;
$body$;

WITH all_started AS (
  SELECT lower(split_part(target_key,':',1)) network,
         (COALESCE(publication_started_at,created_at) AT TIME ZONE 'America/Campo_Grande')::date day
  FROM public.cortes_publications
  WHERE publication_started_at IS NOT NULL OR status IN ('started','confirmed','uncertain')
  UNION ALL
  SELECT 'tiktok', (COALESCE(publication_started_at,created_at) AT TIME ZONE 'America/Campo_Grande')::date
  FROM public.cortes_tiktok_publications
  WHERE publication_started_at IS NOT NULL OR status IN ('started','confirmed','uncertain')
)
INSERT INTO public.cortes_daily_publication_budget(target_key,local_day,reserved,updated_at)
SELECT 'platform:'||network,day,LEAST(100,count(*)::int),now()
FROM all_started WHERE network ~ '^[a-z][a-z0-9_-]{0,30}$'
GROUP BY network,day
ON CONFLICT (target_key,local_day) DO UPDATE
  SET reserved=GREATEST(public.cortes_daily_publication_budget.reserved,EXCLUDED.reserved),updated_at=now();

-- Quotas derive from recorded publication starts. An operational ceiling of
-- 100 does not assert that 100 external posts took place on a given day.
-- Manual corrections require verified evidence and must not be embedded here.

DO $triggers$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='cortes_all_platform_daily_cap_100' AND tgrelid='public.cortes_publications'::regclass) THEN
  CREATE TRIGGER cortes_all_platform_daily_cap_100
    BEFORE INSERT OR UPDATE OF status,publication_started_at
    ON public.cortes_publications
    FOR EACH ROW EXECUTE FUNCTION public.cortes_platform_daily_cap_100();
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='cortes_tiktok_platform_daily_cap_100' AND tgrelid='public.cortes_tiktok_publications'::regclass) THEN
  CREATE TRIGGER cortes_tiktok_platform_daily_cap_100
    BEFORE INSERT OR UPDATE OF status,publication_started_at
    ON public.cortes_tiktok_publications
    FOR EACH ROW EXECUTE FUNCTION public.cortes_platform_daily_cap_100();
 END IF;
END;
$triggers$;
