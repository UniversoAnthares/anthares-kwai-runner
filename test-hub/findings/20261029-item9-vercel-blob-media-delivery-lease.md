# Item fixo 9 — Vercel Blob como rota de mídia Threads (fase 1)
STATUS: RUNNING
AREA: threads/cloud-delivery-media
DATE: 2026-10-29 UTC
RUN: https://vercel.com/lucasyahn-6808/anthares-cortes-cloud-media-qa/D5KvEGXvspA1mLca6qC7JNpEs3fG
JOB: Vercel deployment dpl_D5KvEGXvspA1mLca6qC7JNpEs3fG
COMMIT: ee7fb4b9f5a0e76062de0517a98d63779f34b9a4
SUPERSEDES: none
LEASE: feature/item9-vercel-blob-delivery-20261029-ee7fb4b; source-only, expires after PR closure and append-only result.

## Lista fixa (11 itens, sem renumerar)
Apenas item 9 passa a ter subopções de transporte de mídia: A Vercel Blob (ativa), B subdomínio próprio sem CDN Hostinger (reserva), C Cloudflare R2 (reserva), D Anthares Media Gateway (redundância futura). Os demais itens 1–8 e 10–11 mantêm escopo e numeração.

## BASELINE_PROVEN
Neon 2026-10-29 17:31Z: Threads 195 confirmed, 99 queued, 1 failed, 98 isolados MEDIA_HTTP_403, 1 isolado EDITORIAL_MISSING; cloud_primary_enabled=false. Hostinger origin contém arquivo 7868–7908. Vercel Blob: objeto exato threads/fOmihuHUT1M/g1-7868-7908-7355d6c5358f.mp4 criado, HTTP 200 GET, SHA256 7355d6c5358fdd81a53c93bff17275259bb57f15e44cbe639f95639f0b5cef96, bytes=2090126, verificado no build Vercel. Origem HTTP 200 e SHA PASS. URL https://izu4hsz4kmpqtwkl.public.blob.vercel-storage.com/threads/fOmihuHUT1M/g1-7868-7908-7355d6c5358f.mp4 .

## Objetivo
Permitir apenas o objeto acima como URL alternativa de entrega para o corte original exato, após validação do hash e do atestado de transcrição; reservar no Neon sempre pela URL canônica WordPress existente, nunca sobrescrever identidade/contrato. O bloqueio de quarentena permanece até reconciliação individual autorizada. Nenhum novo post ou incremento de quota é um teste.

## FAILED_AVOIDED
Não alterar a CDN Hostinger, não dispensar SHA/transcrição/caption, não criar outro publicador, não liberar quarentena automaticamente, não reexecutar posts incertos, não trocar o primário nem chamar Codeberg suspenso. Zero PC staging.

## SUCCESS_SIGNAL
Branch/testes verificam mapping exato e reject para origem não correspondente, SHA incompatível e URL externa não allowlisted; transporte Vercel com SHA de origem e destino PASS; PR em estado merged somente após CI.

## FAILURE_SIGNAL
Qualquer media mismatch, URL inesperada, credencial de Vercel exposta, conflito Git/peer, editoria ausente, erro de testes ou duplicação de publisher.

## TEST_VALIDITY
A verificação real de Blob foi upload+GET+SHA do único corte no Vercel. Os testes do código são dry-run/offline, nunca post Graph. Conclusão do item 9 exigirá adicionalmente liberação justificada de quarentena e confirmação individual da postagem sob os gates Neon.
