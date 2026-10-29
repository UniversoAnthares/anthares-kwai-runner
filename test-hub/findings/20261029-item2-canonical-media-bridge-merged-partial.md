# Item fixo 2 — ponte editorial local integrada, execução produtiva Forgejo ainda bloqueada
STATUS: PARTIAL
AREA: tiktok/forgejo-producer-handoff
DATE: 2026-10-29 UTC
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40906681336
JOB: 123563244201
COMMIT: e1cec29aab7a3deddbb76eb5505047374874c88a
SUPERSEDES: 20261029-item2-local-editorial-bridge-lease.md; 20261029-item2-hosted-contract-extension.md
LEASE: ENCERRADO para alterações em UniversoAnthares/anthares-clipper; não se reservou nem se promoveu a admissão produtiva.

EVIDENCE:
- Forgejo WordPress tinha preflight histórico run #238 SUCCESS mas o producer local obtinha state por WP-CLI e attachment metadata por WP HTTP dependente de env WP_SITE_URL indisponível: eligible tinha fail-closed com zero candidatos por metadado.
- PR UniversoAnthares/anthares-clipper #226 MERGED, SHA e1cec29aab7a3deddbb76eb5505047374874c88a, files cortes_tiktok_enqueue.py, cortes_editorial_transport.py, cortes_forgejo_wp_bridge.php, tests/test_cortes_tiktok_enqueue.py.
- Nova rota WP-CLI 'media', read-only, usuário WordPress scoped, IDs de attachment somente, até 100 por chamada. Producer consulta no máximo dois lotes de mídia por tick de 200; valida título, descrição, SEO e suffix do attachment canônico antes de admitir Neon. Nenhuma credencial nova ou leitura da senha.
- Suite unitária do producer (14 testes incluindo batch media, metadata canônica e fail closed) no GitHub Actions run #40906681336, job #123563244201: SUCCESS com todos steps SUCCESS. Workflow do CI foi restaurado ao runner Windows original; hosted experimental run #40907518620 falhou sem steps/logs e não é evidência de regressão do código.
- Clipper Hostinger Forgejo bare refs/heads/main readback e1cec29aab7a3deddbb76eb5505047374874c88a: MATCH; WordPress source SHA 3df318c4690bad78e127c4a29d979d5175cbb409.
- Neon read: cortes_tiktok_publications 414 confirmed, 118 queued, 10 uncertain, todas sem lease ativo na consulta anterior. Novos ingressos entre 12:28 e 14:56 UTC não provam o autor do enfileiramento.

PENDING:
- GitHub repo variable CORTES_FORGEJO_PRODUCER_ENABLED=true permanece não comprovada. A guarda GitHub do produtor + relay existe, sem alteração do cron.
- Variável Forgejo no repo anthares-wordpress permanece sem configuração autorizada comprovada e workflow de enfileiramento real não foi executado.
- A consulta administrativa Forgejo anterior sofreu recusa explícita de segurança; não substituir pela leitura/alteração direta de banco via SSH. Conector Github disponível não expõe CRUD repo Actions variables; gh Windows não autenticado. Browserless excedeu cota grátis; TinyFish wallet negativa. Somente UI/admin legítimo com liberação de controle ou revisão.
- Handoff exige terminar jobs GitHub em curso, alternar uma única autoridade de admissão, executar uma vez o produtor Forgejo e conferir o Neon sem duplicata e com lote real; preserve uncertain de publicação.

ITEM2=PARTIAL: code fix and contract green, not end-to-end Forgejo ownership. No social publishing, state writes or administrative bypass performed.
