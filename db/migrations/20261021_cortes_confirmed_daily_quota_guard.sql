-- Defense-in-depth: a publisher must reserve a daily quota on "started".
-- If a legacy/third-party adapter tries to bypass that state and write
-- "confirmed" directly, allocate an independent 100/day reservation first.
-- A previously started job has already reserved its slot and is not counted
-- twice. The quota table is shared across Buffer and other approved routes.
-- This is additive and does not change previously published media.

INSERT INTO public.cortes_daily_publication_budget(target_key,local_day,reserved)
SELECT target_key,
       (COALESCE(publication_started_at,updated_at)
        AT TIME ZONE 'America/Campo_Grande')::date,
       least(count(*),100)::int
FROM public.cortes_publications
WHERE (publication_started_at IS NOT NULL OR status='confirmed')
  AND target_key IN (
    'kwai:lucasrosalem','linkedin:primary',
    'instagram:universoanthares','pinterest:lucasyahn')
GROUP BY target_key,
  (COALESCE(publication_started_at,updated_at)
   AT TIME ZONE 'America/Campo_Grande')::date
ON CONFLICT(target_key,local_day) DO UPDATE
SET reserved=GREATEST(
    public.cortes_daily_publication_budget.reserved, EXCLUDED.reserved),
    updated_at=now();

CREATE OR REPLACE FUNCTION public.cortes_reserve_direct_confirmation_100()
RETURNS trigger
LANGUAGE plpgsql
SET search_path=pg_catalog,public
AS $quota$
DECLARE
  v_local_day date;
  updated_total integer;
BEGIN
  IF NEW.status <> 'confirmed'
     OR NEW.target_key NOT IN (
         'kwai:lucasrosalem','linkedin:primary',
         'instagram:universoanthares','pinterest:lucasyahn')
  THEN
    RETURN NEW;
  END IF;

  IF TG_OP='UPDATE' THEN
    IF OLD.status='confirmed' OR OLD.publication_started_at IS NOT NULL
    THEN
      RETURN NEW;
    END IF;
  END IF;

  v_local_day:=(now() AT TIME ZONE 'America/Campo_Grande')::date;
  INSERT INTO public.cortes_daily_publication_budget(
    target_key,local_day,reserved,updated_at)
  VALUES(NEW.target_key,v_local_day,1,now())
  ON CONFLICT(target_key,local_day)
  DO UPDATE SET reserved=public.cortes_daily_publication_budget.reserved+1,
                updated_at=now()
    WHERE public.cortes_daily_publication_budget.reserved<100
  RETURNING reserved INTO updated_total;

  IF updated_total IS NULL THEN
    RAISE EXCEPTION USING MESSAGE='CORTES_DAILY_PUBLICATION_LIMIT_100',
                          ERRCODE='P0001';
  END IF;
  NEW.publication_started_at=COALESCE(NEW.publication_started_at,now());
  RETURN NEW;
END;
$quota$;

DO $install$
BEGIN
 IF NOT EXISTS (
   SELECT 1 FROM pg_trigger
   WHERE tgname='cortes_direct_insert_confirm_quota_100'
     AND tgrelid='public.cortes_publications'::regclass
     AND NOT tgisinternal
 ) THEN
   CREATE TRIGGER cortes_direct_insert_confirm_quota_100
   BEFORE INSERT ON public.cortes_publications
   FOR EACH ROW WHEN (NEW.status='confirmed')
   EXECUTE FUNCTION public.cortes_reserve_direct_confirmation_100();
 END IF;

 IF NOT EXISTS (
   SELECT 1 FROM pg_trigger
   WHERE tgname='cortes_direct_update_confirm_quota_100'
     AND tgrelid='public.cortes_publications'::regclass
     AND NOT tgisinternal
 ) THEN
   CREATE TRIGGER cortes_direct_update_confirm_quota_100
   BEFORE UPDATE OF status ON public.cortes_publications
   FOR EACH ROW
   WHEN (NEW.status='confirmed' AND OLD.status IS DISTINCT FROM NEW.status)
   EXECUTE FUNCTION public.cortes_reserve_direct_confirmation_100();
 END IF;
END;
$install$;
