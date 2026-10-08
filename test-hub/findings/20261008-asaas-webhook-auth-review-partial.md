# Asaas webhook authorization static review
STATUS: PARTIAL
AREA: wordpress-payments
DATE: 2026-10-08
RUN: none
JOB: none
COMMIT: 85aa1ed09076ba18bc880f397fe3e8a01afe9e09
SUPERSEDES: none

Review of anthares-pix-sales/includes/67-asaas-recebimentos.php and 67-repasses-asaas-validacao-saque.php at WordPress main. Both public WordPress REST routes use permission_callback=__return_true, but their callbacks explicitly compare asaas-access-token with hash_equals before payment settlement or withdrawal approval. Thus public routing is intentional for webhook delivery, not proof of unauthenticated approval. Withdrawal authorization fails closed with REFUSED when no secret is configured and uses a replay/idempotence decision table. Receipt webhook marks event seen after successful processing. No production transaction performed.

Potential reliability edge case to reproduce before editing: anthares_loja_asaas_recebimentos_webhook_token() regenerates a webhook token when a stored encrypted token cannot be decrypted, potentially causing remote Asaas deliveries to fail until provider token is updated. Do not change the live token or regenerate it as an audit probe. Test in an isolated WordPress fixture before proposing a patch.

No financial authorization or live payment approval is claimed. No secrets recorded.