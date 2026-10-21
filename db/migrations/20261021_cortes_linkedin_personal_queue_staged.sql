-- CORTES 2026-10-21: second LinkedIn destination is the member administering
-- corporate Universo Anthares; keep account-specific queue keys and quotas.
-- This is a queue-only change. No personal LinkedIn publisher is activated.
-- Existing AFTER INSERT/UPDATE triggers call this same function; no trigger
-- reinstall, counter reset or status changes are required.
-- Every destination insert is individually exception-isolated/idempotent.
CREATE OR REPLACE FUNCTION public.cortes_kwai_short_social_fanout()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, public
AS $cortes$
DECLARE
    segment text;
    video_url text;
    clip_title text;
    attachment_text text;
    attachment_id bigint;
    calculated_sha text;
    destination record;
    social_id text;
    local_day date;
BEGIN
    IF NEW.target_key <> 'kwai:lucasrosalem'
       OR NEW.duration_class <> 'short'
       OR NEW.source_end - NEW.source_start NOT BETWEEN 30 AND 90
       OR NEW.status = 'failed'
    THEN
       RETURN NEW;
    END IF;

    local_day := (now() AT TIME ZONE 'America/Campo_Grande')::date;
    IF (NEW.created_at AT TIME ZONE 'America/Campo_Grande')::date <> local_day THEN
       RETURN NEW;
    END IF;

    segment := NULLIF(NEW.payload->>'segment_id', '');
    video_url := NULLIF(NEW.payload->>'video_url', '');
    clip_title := COALESCE(NULLIF(NEW.payload->>'title', ''),
                           NULLIF(NEW.payload->>'video_title', ''));
    attachment_text := NEW.payload->>'cortes_attachment_id';
    IF segment IS NULL OR video_url IS NULL OR clip_title IS NULL
       OR attachment_text IS NULL
       OR attachment_text !~ '^[0-9]{1,9}$'
       OR split_part(video_url, '/', 1) <> 'https:'
       OR split_part(video_url, '/', 3) NOT IN ('anthares.us', 'www.anthares.us')
       OR right(video_url, 4) <> '.mp4'
    THEN
       RETURN NEW;
    END IF;

    attachment_id := attachment_text::bigint;
    IF attachment_id <= 0 THEN RETURN NEW; END IF;
    calculated_sha := encode(sha256(convert_to(
       NEW.source_id || '|' || segment || '|' || video_url, 'UTF8')), 'hex');
    IF NEW.media_sha256 <> calculated_sha THEN RETURN NEW; END IF;

    FOR destination IN
       SELECT * FROM (VALUES
         ('linkedin'::text,'linkedin:primary'::text,'primary'::text),
         ('linkedin'::text,'linkedin:personal'::text,'personal'::text),
         ('instagram'::text,'instagram:universoanthares'::text,'universoanthares'::text),
         ('pinterest'::text,'pinterest:lucasyahn'::text,'lucasyahn'::text)
       ) AS d(platform,target_key,account_id)
    LOOP
       BEGIN
          -- All eligible short masters are registered, regardless of count.
          -- The network workers enforce provider rate limits independently;
          -- a blocked channel must not prevent creation for the others.
          social_id := 'cortes-fanout-' || destination.platform || '-' ||
              substring(encode(sha256(convert_to(NEW.source_id || '|' || segment ||
                        '|' || destination.target_key, 'UTF8')), 'hex'), 1, 32);

          INSERT INTO public.cortes_publications(
             id,dedupe_key,target_key,master_id,media_sha256,source_id,
             source_start,source_end,duration_class,payload)
          VALUES(
             social_id,social_id,destination.target_key,NEW.source_id,
             NEW.media_sha256,NEW.source_id,NEW.source_start,NEW.source_end,'short',
             jsonb_build_object(
               'id',social_id,'dedupe_key',social_id,'executor','social_video',
               'platform',destination.platform,'target_key',destination.target_key,
               'account_id',destination.account_id,'master_id',NEW.source_id,
               'source_id',NEW.source_id,'segment_id',segment,'duration_class','short',
               'duration_seconds',NEW.source_end-NEW.source_start,
               'source_start',NEW.source_start,'source_end',NEW.source_end,
               'media_sha256',NEW.media_sha256,'media_hash_kind','dispatch_identity',
               'media_url',video_url,'video_url',video_url,'title',clip_title,
               'video_title',clip_title,'cortes_attachment_id',attachment_id,
               'planned_at',COALESCE(NEW.payload->>'planned_at',''),
               'round_date',to_char(local_day,'YYYY-MM-DD')
             ))
          ON CONFLICT DO NOTHING;
       EXCEPTION WHEN OTHERS THEN
          -- Each social network is isolated. Kwai and other networks continue.
          BEGIN
             INSERT INTO public.cortes_social_fanout_errors(
                 target_key,source_id,segment_id,reason)
             VALUES(destination.target_key,NEW.source_id,segment,SQLSTATE)
             ON CONFLICT(target_key,source_id,segment_id)
             DO UPDATE SET attempts=cortes_social_fanout_errors.attempts+1,
                           reason=EXCLUDED.reason,last_seen_at=now();
          EXCEPTION WHEN OTHERS THEN
             NULL; -- Last resort: never abort a Kwai job to report social QA.
          END;
       END;
    END LOOP;

    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    -- Invalid source metadata must not interrupt Kwai publication.
    RETURN NEW;
END;
$cortes$;
