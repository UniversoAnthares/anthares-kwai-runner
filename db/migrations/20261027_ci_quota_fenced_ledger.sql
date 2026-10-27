-- Additive proposal only: no production deployment or privileges in this PR.
-- Never reclaim an expired attempt automatically: reconcile remote status first.
CREATE TABLE public.anthares_ci_quota_attempts (
    attempt_id text PRIMARY KEY,
    owner_token uuid NOT NULL,
    lease_generation bigint NOT NULL DEFAULT 1 CHECK (lease_generation > 0),
    state text NOT NULL,
    data jsonb NOT NULL,
    lease_until timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
REVOKE ALL ON public.anthares_ci_quota_attempts FROM PUBLIC;
CREATE INDEX anthares_ci_quota_attempts_expiry_idx
    ON public.anthares_ci_quota_attempts (lease_until);
