# TikTok publisher exige prova pós-publicação no perfil
STATUS: PROVEN
AREA: tiktok-publish
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: 2eb0d9bfabf60e3e597fa46a6c7f58a9e4c10c79
SUPERSEDES: test-hub/findings/20261005-1945-chat3-tiktok-publish-profile-verification-lease.md

BASELINE_PROVEN: o pipeline valida previamente a conta TikTok exata; inventory_profile_videos() opera em modo read-only no perfil alvo autenticado e coleta IDs/URLs por rede, hidratação, API e DOM; o publisher já exigia confirmação inequívoca de UI; o caller central já envia remote_id ou confirmation_evidence ao ledger fail-closed.
FAILED_AVOIDED: clique/feedback de UI isolado deixou de bastar para confirmar o job; zero candidatos novos, múltiplos candidatos novos e divergência entre ID da URL pós-publicação e ID novo do perfil são estados ambíguos e terminam em erro para reconciliação; nenhum canário real foi disparado com sessão bloqueada.
SUCCESS_SIGNAL: inventário imediatamente anterior ao upload + confirmação de UI + exatamente um ID novo no perfil + concordância com o ID da URL quando disponível; somente então evidence.confirmed=true com remote_id real e confirmation=profile_new_post.
FAILURE_SIGNAL: publisher confirmar com zero/múltiplos IDs novos, aceitar divergência de IDs ou produzir TIKTOK_OWNED_PUBLISH=OK sem remote_id real.
TEST_VALIDITY: revisão do diff final e do arquivo atual confirma as guardas; simulação da função de comparação validou zero candidato, deduplicação de um candidato e múltiplos candidatos. Prova de código/simulação; integração real depende de sessão TikTok PROVEN e de um canário.

## Objetivo
Transformar a confirmação do publisher em prova pós-publicação ligada ao perfil universo.anthares e obter um remote_id real antes de concluir o ledger.

## Resultado
PROVEN em código. Commit d669748e0dfb4cded87b7c2db6c238f30ff52179 adicionou inventário pré/pós e exige exatamente um vídeo novo. Commit 2eb0d9bfabf60e3e597fa46a6c7f58a9e4c10c79 acrescentou concordância entre o ID da URL pós-confirmação e o ID novo do perfil quando a URL expõe /video/<id>. A evidência final contém remote_id real, remote_url, confirmation=profile_new_post e ui_confirmation=ui_success.

## Evidência decisiva
O arquivo atual tiktok_web_publish_local.py registra o baseline de IDs antes do upload, repete o inventário pós-publicação até três vezes, aceita apenas len(candidates)==1, rejeita múltiplos, rejeita ausência após as tentativas e rejeita divergência com o ID da URL. TIKTOK_OWNED_PUBLISH=OK agora sempre inclui o remote_id validado.

## Consequência
LEASE tiktok-publish encerrado para esta lacuna. O código novo está em main do anthares-clipper. O serviço Render observado continua na revisão 1917fb3579693b2725658e004fcb109a75b7af76; portanto esta mudança ainda não está comprovada no executor Render em produção. Evitar deploy causal concorrente enquanto tiktok-session depende do control plane. Após sessão/identidade PROVEN, implantar a revisão publisher escolhida e executar exatamente um canário real; somente a combinação post real + remote_id validado permitirá classificar PRODUCTION PROVEN.
