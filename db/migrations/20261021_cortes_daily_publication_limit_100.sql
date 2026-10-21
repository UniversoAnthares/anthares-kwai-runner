-- CORTES global policy: at most 100 publication attempts per destination,
-- per calendar day America/Campo_Grande. This is NOT a Buffer quota.
-- Do not cap durable enqueue/fanout: preserve every eligible master and route
-- delivery through independently authenticated, provider-compliant consumers.
-- Using an atomic PostgreSQL counter prevents concurrent workers, Buffer and
-- future direct adapters from exceeding the CORTES-wide 100-per-day budget.
--
-- First transition to started reserves one unit. An uncertain or failed
-- attempt retains its reservation; do not grant a second attempt accidentally.
-- Each target_key has its own counter. Quota denial to Pinterest, for example,
-- cannot block starting a LinkedIn or Instagram delivery.
CREATE TABLE IF NOT EXISTS public.cortes_daily_publication_budget (
  target_key text NOT NULL,
  local_day date NOT NULL,
  reserved integer NOT NULL DEFAULT 0 CHECK (reserved BETWEEN 0 AND 100),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (target_key, local_day)
);

INSERT INTO public.cortes_daily_publication_budget(target_key,local_day,reserved)
SELECT target_key,
       (publication_started_at AT TIME ZONE 'America/Campo_Grande')::date,
       least(count(*),100)::int
  FROM public.cortes_publications
 WHERE publication_started_at IS NOT NULL
   AND target_key IN (
     'kwai:lucasrosalem','linkedin:primary',
     'instagram:universoanthares','pinterest:lucasyahn')
 GROUP BY target_key,(publication_started_at AT TIME ZONE 'America/Campo_Grande')::date
ON CONFLICT (target_key,local_day) DO UPDATE
  SET reserved=GREATEST(
         public.cortes_daily_publication_budget.reserved,
         EXCLUDED.reserved),
      updated_at=now();

CREATE OR REPLACE FUNCTION public.cortes_reserve_daily_publication_100()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog,public
AS $cortes$
DECLARE
  local_day date;
  updated_total integer;
BEGIN
  IF NEW.status <> 'started'
     OR OLD.status = 'started'
     OR OLD.publication_started_at IS NOT NULL
     OR NEW.target_key NOT IN (
        'kwai:lucasrosalem','linkedin:primary',
        'instagram:universoanthares','pinterest:lucasyahn')
  THEN
    RETURN NEW;
  END IF;

  local_day:=(now() AT TIME ZONE 'America/Campo_Grande')::date;
  INSERT INTO public.cortes_daily_publication_budget(
    target_key,local_day,reserved,updated_at)
  VALUES(NEW.target_key,local_day,1,now())
  ON CONFLICT(target_key,local_day)
  DO UPDATE SET reserved=public.cortes_daily_publication_budget.reserved+1,
                updated_at=now()
    WHERE public.cortes_daily_publication_budget.reserved<100
  RETURNING reserved INTO updated_total;

  IF updated_total IS NULL THEN
    RAISE EXCEPTION USING
      MESSAGE='CORTES_DAILY_PUBLICATION_LIMIT_100',
      ERRCODE='P0001';
  END IF;
  NEW.publication_started_at=COALESCE(NEW.publication_started_at,now());
  RETURN NEW;
END;
$cortes$;

DROP TRIGGER IF EXISTS cortes_daily_publication_limit_100 ON public.cortes_publications;
CREATE TRIGGER cortes_daily_publication_limit_100
BEFORE UPDATE OF status ON public.cortes_publications
FOR EACH ROW
WHEN (NEW.status = 'started' AND OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION public.cortes_reserve_daily_publication_100();
