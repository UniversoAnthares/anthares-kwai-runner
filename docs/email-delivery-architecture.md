# Anthares Email Delivery Architecture

Status: prepared, no bulk campaign authorized.

## Pipeline
contacts -> validation -> segmentation -> campaign -> queue -> provider -> delivery_result -> bounce/unsubscribe -> reporting

## Contact contract
Each contact stores normalized_email, display_name, source, source_ref, acquired_at, consent_basis/status when known, tags/segments, validation_status, last_validation_at and suppression_status. Normalized email is the dedupe identity. Provenance is append-only.

## Campaign gate
A campaign cannot enter QUEUED until campaign_approved=true and recipient_set_approved=true. The future pastors campaign must remain DRAFT until both approvals exist.

## Queue contract
States: DRAFT, QUEUED, LEASED, SENT, DELIVERED, BOUNCED, COMPLAINED, UNSUBSCRIBED, FAILED, SUPPRESSED.
Every item carries campaign_id, contact_id, provider, provider_message_id, attempts, lease_owner, lease_expires_at, created_at, sent_at and last_event_at.
Suppression is checked again immediately before provider dispatch.

## Provider routing
PRIMARY_CAMPAIGN: Brevo, already authorized by anthares.us SPF and suitable for gradual campaign sending.
SECONDARY_CAMPAIGN: Resend after explicit connection/domain verification.
MAILBOX/REPLY: Hostinger contato@anthares.us.
Gmail remains an independent human mailbox path and is not the bulk-campaign transport.

Provider failure affects only that delivery item. Retry may change provider only when the alternate provider has authenticated domain alignment and the same suppression gate.

## Deliverability
Current DNS audit 2026-10-06:
- MX: mx1.hostinger.com (10), mx2.hostinger.com (20)
- SPF: v=spf1 include:_spf.mail.hostinger.com include:spf.brevo.com ~all
- DMARC: v=DMARC1; p=none; rua=mailto:rua@dmarc.brevo.com
- Hostinger DKIM selector hostingermail-a resolves to hostingermail-a.dkim.mail.hostinger.com
- Brevo domain verification TXT is present.

DMARC remains monitoring-only. Raise enforcement only after provider DKIM/alignment and reporting are verified for every active sender.

## Rate policy
Use gradual batches with per-provider caps below provider limits. The scheduler must support daily caps, hourly caps, jitter and pause-on-bounce/complaint thresholds. No campaign code may infer permission to send from the existence of a contact.

## Bounce and unsubscribe
Hard bounce, complaint and unsubscribe immediately create/refresh a global suppression entry keyed by normalized_email. Soft bounces increment a counter and become suppressed after a configured threshold. Every marketing template must carry a functional unsubscribe URL/token. Suppression entries override campaign membership and retries.

## Templates
Templates are versioned by template_id + version. Required fields: subject, html/text body, sender identity, reply-to, unsubscribe placeholder, campaign purpose, locale. Pastor templates remain placeholders until campaign copy is approved.

## Reporting
Aggregate by campaign/provider: queued, sent, delivered, bounced hard/soft, complaints, unsubscribes, failures and suppressed-before-send. Never store provider secrets in reports or Test Hub.
