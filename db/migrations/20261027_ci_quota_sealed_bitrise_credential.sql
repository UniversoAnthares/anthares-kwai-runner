-- Bitrise one-time RSA-OAEP encrypted credential delivery.
-- Separate strict table preserves AppVeyor's provider='appveyor' CHECK unchanged.
CREATE TABLE IF NOT EXISTS public.anthares_ci_quota_sealed_bitrise (
  provider text PRIMARY KEY CHECK (provider='bitrise'),
  sealed_ciphertext text NOT NULL CHECK(length(sealed_ciphertext) BETWEEN 480 AND 540),
  source_run text NOT NULL,
  expires_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
REVOKE ALL ON TABLE public.anthares_ci_quota_sealed_bitrise FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.anthares_ci_quota_sealed_bitrise TO anthares_ci_quota_limited;
