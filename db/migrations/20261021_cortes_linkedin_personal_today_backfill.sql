-- Stage all already queued company LinkedIn cuts for the linked member as a
-- separate, unconsumed destination. Never copy a company remote_id or proof.
-- Preserves the original source identity, media hash and daily round.
-- Idempotent: identical (source,segment,target) always produces the same id.
-- No publishing, token changes, scheduled tasks or lease are created.
INSERT INTO public.cortes_publications(
  id,dedupe_key,target_key,master_id,media_sha256,source_id,
  source_start,source_end,duration_class,payload,created_at
)
SELECT
  personal.id,personal.id,'linkedin:personal',org.master_id,
  org.media_sha256,org.source_id,org.source_start,org.source_end,
  org.duration_class,
  org.payload || jsonb_build_object(
    'id',personal.id,'dedupe_key',personal.id,'target_key','linkedin:personal',
    'account_id','personal','platform','linkedin'),
  org.created_at
FROM public.cortes_publications AS org
CROSS JOIN LATERAL (
  SELECT 'cortes-fanout-linkedin-' ||
    substring(encode(sha256(convert_to(
      org.source_id || '|' || (org.payload->>'segment_id') ||
      '|linkedin:personal','UTF8')),'hex'),1,32) AS id
) AS personal
WHERE org.target_key='linkedin:primary'
  AND org.duration_class='short'
  AND org.payload->>'segment_id' IS NOT NULL
  AND (org.created_at AT TIME ZONE 'America/Campo_Grande')::date =
      (now() AT TIME ZONE 'America/Campo_Grande')::date
ON CONFLICT DO NOTHING;
