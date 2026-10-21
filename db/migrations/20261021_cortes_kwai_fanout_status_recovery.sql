-- Secondary self-healing fanout trigger.
-- Existing trigger fires on INSERT and payload/media changes. This independent
-- trigger also repairs missed social delivery rows when the Kwai job advances
-- status (e.g. queued -> started / started -> uncertain / confirmed).
-- The shared fanout function uses deterministic IDs and ON CONFLICT DO NOTHING.
-- No video is republished, no media deleted, and no other network is blocked.
DO $install$
BEGIN
  IF NOT EXISTS (
     SELECT 1 FROM pg_trigger
     WHERE tgname='cortes_kwai_social_fanout_status_recovery'
       AND tgrelid='public.cortes_publications'::regclass
       AND NOT tgisinternal
  ) THEN
    CREATE TRIGGER cortes_kwai_social_fanout_status_recovery
    AFTER UPDATE OF status ON public.cortes_publications
    FOR EACH ROW
    WHEN (NEW.target_key='kwai:lucasrosalem' AND
          OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION public.cortes_kwai_short_social_fanout();
  END IF;
END
$install$;
