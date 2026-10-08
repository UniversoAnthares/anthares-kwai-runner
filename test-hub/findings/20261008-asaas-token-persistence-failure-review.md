# Asaas webhook token persistence and rotation risk
STATUS: PARTIAL
AREA: wordpress-payments
DATE: 2026-10-08
RUN: none
JOB: static-review
COMMIT: 85aa1ed09076ba18bc880f397fe3e8a01afe9e09
SUPERSEDES: none

Reviewed complete relevant function `anthares_loja_asaas_recebimentos_webhook_token()` in `anthares-pix-sales/includes/67-asaas-recebimentos.php` from GitHub main blob `7546c56288b68b10d64a8dd82d6ea8efaec3da4f`.

Evidence: when `get_option` yields a nonempty stored token but `anthares_repasses_decrypt` cannot recover a >=32-character value, the function proceeds to generate a new random token rather than fail closed. Further, if `anthares_repasses_encrypt` returns a false value, `update_option` is skipped but the generated token is returned; if `update_option` itself fails, return is also unchecked. Both scenarios can produce an ephemeral webhook secret inconsistent with the persisted value, disrupting Asaas deliveries.

Safe proposed correction (NOT DEPLOYED): if nonempty stored token fails decryption, return empty string (deny) and alert administrators rather than rotate; for initial provisioning, generate once, require successful encryption and persistence, then read back and verify before returning. Account for WordPress `update_option` false on unchanged value. Add isolated unit tests for corrupt ciphertext, encryption failure, DB write failure, and valid existing ciphertext before changing production. No live webhook token changed or payment attempted.
