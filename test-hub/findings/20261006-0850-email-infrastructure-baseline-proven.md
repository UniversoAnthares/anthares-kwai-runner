# Email infrastructure audit — redundant provider baseline
STATUS: PROVEN
AREA: email
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: test-hub/findings/20261006-0845-lease-email-infrastructure-audit.md

## Objetivo
Prepare the future pastors campaign infrastructure without sending a campaign.

## Resultado
PROVEN baseline. Hostinger Mail API is connected and exposes contato@anthares.us, send/read operations and an active message.received webhook to the Anthares WordPress endpoint. DNS proves Hostinger MX, combined Hostinger+Brevo SPF, DMARC reporting in p=none, Hostinger DKIM, and Brevo domain verification. Gmail is independently connected. A provider-neutral queue/suppression/unsubscribe architecture was added in docs/email-delivery-architecture.md. No bulk email was sent.

Brevo is the strongest already-configured campaign path. Resend is a technically suitable second campaign provider once the user connects it and completes domain verification. Its current free tier is 3,000/month and 100/day; Brevo free is 300/day. Hostinger remains mailbox/reply transport and should not absorb campaign bursts.

## Evidência decisiva
DNS on 2026-10-06 resolved anthares.us MX to mx1.hostinger.com/mx2.hostinger.com; SPF to include both _spf.mail.hostinger.com and spf.brevo.com; _dmarc to p=none with Brevo aggregate reporting; hostingermail-a DKIM CNAME resolved. Hostinger API GET /api/v1/me returned contato@anthares.us and GET webhooks returned active Anthares E-mail Automático for message.received.

## Consequência
Future pastor campaign stays DRAFT until explicit campaign + recipient-list approval. Implement/import contacts with provenance and dedupe, then validate/suppress before queueing. Preserve Brevo as campaign primary and Hostinger as mailbox path. Add Resend only after explicit connection/domain verification. Do not bulk-send through Gmail or Hostinger merely because their connectors can send.
