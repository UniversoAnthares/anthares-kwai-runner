# Publicação de vídeos sem legenda — Kwai, Threads e TikTok

Contrato operacional autorizado em 2026-11-12.

1. Para vídeos, legenda/caption é opcional nas três redes. No Kwai físico, tentar publicar com campo vazio desde o início. Em Threads e TikTok, se a única falha estiver na criação/inserção da legenda, prosseguir com vídeo sem legenda.
2. Um campo com texto antigo ou parcialmente digitado precisa ser limpo e verificado vazio. Se essa limpeza falhar, bloquear a tentativa antes de clicar em Publicar. Nunca publicar texto de outro vídeo.
3. Preservar todos os requisitos de conta autenticada e identidade exata, mídia/segmento/hash, limites por conta e dia, intervalo calculado até 23h, autorização OAuth quando aplicável, visibilidade pública, lease e deduplicação.
4. Distinguir falha de legenda de falha de autenticação, privacidade, mídia, upload, CAPTCHA, bloqueio de plataforma ou cota. A exceção de legenda não se aplica a esses problemas.
5. O ponto irreversível é o clique final em Publicar ou a chamada final da API. É proibido repetir o clique/call após resultado incerto. Reconciliar com o perfil real, ID/URL e evidência de mídia.
6. Com legenda vazia, a prova deixa de depender de correspondência textual: Kwai compara quadros do vídeo e identidade/tempo da publicação; Threads exige ID retornado pela API ou um único novo post na listagem autenticada; TikTok exige um único novo ID de vídeo no TikTok Studio autenticado. Persistir a origem editorial separadamente.
7. Se a plataforma passar a exigir legenda para publicar, registrar bloqueio específico e preservar a tentativa sem criar publicação incerta ou falsa confirmação. Não ignorar desafios de segurança.

Implementação:
- `tools/kwai_native_cortes.py`, `tools/kwai_physical_public_proof.py` e `tools/kwai_physical_queue_daemon.py`: fluxo local com `ANTHARES_KWAI_CAPTION_OPTIONAL=1`, leitura do editor vazio, prova independente e confirmação de mídia.
- `tools/cortes_threads_local_publisher.mjs`: recuperação de campo de texto, remoção de conteúdo residual e reconciliação por novo post.
- `tools/cortes_threads_cloud_handoff.mjs`: somente erro explícito de legenda na criação de contêiner permite uma tentativa de contêiner sem texto; nenhum retry do `threads_publish`.
- `tools/cortes_tiktok_lucasrosalem4_cloud_publish.py`: falha específica de legenda, limpeza do editor, única nova publicação no Studio; não reutilizar marcador de legenda inexistente.
