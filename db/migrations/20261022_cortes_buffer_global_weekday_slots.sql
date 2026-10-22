-- All CORTES Buffer channels share a hard maximum of 20 deliveries per
-- local weekday (Monday to Friday, America/Campo_Grande). Saturday/Sunday
-- allocations are impossible at the PostgreSQL schema level.
-- A slot is claimed in the same SQL statement as a fenced Neon queue lease.
CREATE TABLE IF NOT EXISTS public.cortes_buffer_daily_slots (
  local_day date NOT NULL,
  slot smallint NOT NULL,
  target_key text NOT NULL,
  job_id text NOT NULL,
  reserved_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT cortes_buffer_slot_day_pk PRIMARY KEY(local_day,slot),
  CONSTRAINT cortes_buffer_slot_unique_job_day UNIQUE(local_day,job_id),
  CONSTRAINT cortes_buffer_slot_range_check CHECK(slot BETWEEN 1 AND 20),
  CONSTRAINT cortes_buffer_slot_weekday_check CHECK(extract(isodow FROM local_day) BETWEEN 1 AND 5),
  CONSTRAINT cortes_buffer_slot_destination_check
    CHECK(target_key IN ('linkedin:primary','instagram:universoanthares','pinterest:lucasyahn'))
);
CREATE INDEX IF NOT EXISTS cortes_buffer_daily_slots_job_idx
  ON public.cortes_buffer_daily_slots(job_id);
COMMENT ON TABLE public.cortes_buffer_daily_slots IS
  'Global CORTES Buffer allocation ledger; exactly 20 slots per local weekday across all social channels, Sat/Sun prohibited. Non-Buffer publishers do not consume these slots.';
