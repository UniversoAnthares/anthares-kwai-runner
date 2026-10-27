-- Anthares quota sealed credential transport. Stores only RSA-OAEP ciphertext.
-- Private RSA key never leaves Windows SYSTEM DPAPI. No plaintext credentials are stored.
CREATE TABLE IF NOT EXISTS public.anthares_ci_quota_sealed_credentials (
  provider text PRIMARY KEY CHECK (provider = 'appveyor'),
  sealed_ciphertext text NOT NULL CHECK (length(sealed_ciphertext) BETWEEN 480 AND 540),
  source_run text NOT NULL,
  expires_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
REVOKE ALL ON TABLE public.anthares_ci_quota_sealed_credentials FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.anthares_ci_quota_sealed_credentials
  TO anthares_ci_quota_limited;
-- No UNRESTRICTED role, public schema grant, or long-lived plaintext.
