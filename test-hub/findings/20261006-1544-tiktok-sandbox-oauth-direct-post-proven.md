# TikTok Sandbox OAuth + private Direct Post proof
STATUS: PROVEN
AREA: tiktok-session
DATE: 2026-10-06
RUN: none
JOB: AI Commander UI automation jobs 7f8d92b9105ad84d and 2dbf631b8ad10ebe
COMMIT: anthares-wordpress 26db72119315570d44755a2ec0558ab6bb8b700f
SUPERSEDES: 20261006-1500-lease-tiktok-oauth-state-stateless-fix.md

## Objetivo
Fechar o erro OAuth state_error do Sandbox e provar o fluxo oficial Content Posting API com a conta de teste correta.

## Resultado
PROVEN. O state passou a ser assinado/verificável sem depender de transient. A autorização retornou "TikTok Sandbox autorizado". Creator Info confirmou @universo.anthares e SELF_ONLY. Um único Direct Post privado foi acionado pelo painel e o estado exibido pelo painel chegou a PUBLISH_COMPLETE.

## Evidência decisiva
- OAuth autorizado após deploy do commit 26db721.
- Content Posting API: conexão confirmada pelo painel.
- UI Automation: @universo.anthares e opções PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, SELF_ONLY.
- Job 7f8d92b9105ad84d: PRIVATE_POST_TRIGGER=READY e PRIVATE_POST_TRIGGER=CONFIRMED.
- Job 2dbf631b8ad10ebe: PUBLISH_COMPLETE e linha de item "Publicado".

## Consequência
Não repetir autorização nem reenviar o mesmo vídeo. Preservar o state stateless assinado. Próxima etapa é finalizar o MP4 de demonstração/review e usar a prova privada existente; qualquer nova publicação exige novo motivo causal.
