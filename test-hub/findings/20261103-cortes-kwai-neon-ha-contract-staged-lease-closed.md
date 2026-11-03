# CORTES — contrato HA Kwai e migração cloud do reabastecimento preparados
STATUS: PARTIAL
AREA: queue
DATE: 2026-11-03
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2057
JOB: none
COMMIT: 3d61e35a67f48bbdc92ef192df79f58e520e9ea7
SUPERSEDES: 20261103-lease-queue-cortes-kwai-neon-ha-failclosed.md
LEASE_CLOSED_UTC: 2026-11-03T21:41:02.575Z
GOVERNANCE_MANIFEST: 223433740e807a90
OWNER: ChatGPT / Reestruturação e Otimização / CORTES

## Objetivo
Avançar reconciliação de 68 publicações incertas Kwai, completar o contrato da fila Cloudflare/Neon e preparar migração dos workflows CORTES Windows sem violar custos, identidade e proteção contra duplicação.

## Reconciliação — observado diretamente (não inferido)
- Neon projeto principal anthares-ara-ha: em 2026-11-03, alvo kwai:lucasrosalem possui 456 confirmed e 68 uncertain.
- Os 68 possuem publication_started_at; zero remote_id, zero confirmation_evidence, zero pares de mídia SHA idêntica a um registro confirmed e zero intervalos sobrepostos a confirmed do mesmo alvo; três fontes com grupos 51, 16, 1.
- Não há leases ativos. Nenhum registro UNCERTAIN foi atualizado, reenviado ou promovido.
- Confirmar somente com prova pública exata da conta e do vídeo. Os contratos existentes tools/kwai_verify_public_post.py e tools/kwai_physical_public_proof.py validam links Kwai do formato k.kwai.com/p/ID ou www.kwai.com/@handle/photo/ID; exigem verificação de identidade e conta, sem uso de postagem para testes.

## Fila cloud — código STAGED, sem deploy
- PR pública draft #2057 em UniversoAnthares/anthares-kwai-runner, HEAD 3d61e35a67f48bbdc92ef192df79f58e520e9ea7, quatro arquivos: infra/neon-cortes-queue/index.mjs, dois ingressos Cloudflare e teste em tests/.
- Actions: kwai-uncertain-read (OIDC read-only), kwai-enqueue (produtor Clipper allowlisted), kwai-lease/start/confirm/fail (publicador Kwai OIDC allowlisted). Flag de produção CORTES_KWAI_CLOUD_PUBLISH_ENABLED default-off; explicitamente sem deploy.
- Endpoints e credenciais de outros publicadores preservados; a mesma tabela Neon controla dedupe, status, geração do lease e orçamento platform:kwai <=100/dia.
- SQL preserva qualquer UNCERTAIN e bloqueia novos enqueues/leases para o alvo enquanto esses registros exigem reconciliação.
- Confirmação exige URL Kwai suportada, mesma conta, identificação do vídeo, mídia SHA no ledger, método de readback nativo e fencing.
- Sintaxe dos 3 módulos JS e do teste verificada; 5 testes negativos com flag desativada e OIDC indevido + 4 testes negativos com flag simulada (sem DB e sem rede externa): 9/9 PASS.
- Vercel CORTES principal continua HTTP 402; não solicitar upgrade, cobrar ou repetir acesso ao endpoint. Workers cloud já existentes tiveram HTTP 200 health e HTTP 401 para escrita sem credencial; isso é prova da versão anterior, não prova deploy do novo contrato.

## Migração de CORTES — código STAGED, sem corte de produção
- PR privada draft #231 em UniversoAnthares/anthares-clipper, HEAD 53c89840611397fe60b3853e9478c0f30def33e3: troca apenas refill manual para ubuntu-24.04, autenticação OIDC e URL Cloudflare allowlisted, sem cron, token de dispositivo ou caminhos Windows. Requer vars.CORTES_CLOUD_REFILL_ENABLED == '1'; permanece desativado por padrão. Adiciona qa/test_cortes_hosted_refill.py ainda não executado em cloud.
- Os workflows cortes-daily.yml e cortes-short-resume.yml continuam com dependências Windows, mídia local e ledgers que precisam de recuperação remota e contrato de writer único. O preflight hosted de acesso ao código/FFmpeg foi PROVEN no run 41116819377, sem produção.
- As PRs draft não alteraram workflow, banco, Worker ou Neon Functions de produção; CORTES real ficou preservado.

## Pendências e critério terminal
1. Readback público exato das 68 publicações com URLs e conta correta; sem recibo, mantê-las UNCERTAIN e bloquear retry.
2. Prova de identidade e publicação do consumidor Android remoto Kwai com ledger/fencing real, sem postar mídia apenas para testar.
3. Restaurar todos os masters e checkpoints de geração (não apenas uma amostra) em storage externo, com hash e rollback, antes do cutover de daily/resume.
4. Homologar o novo código em ambiente de QA isolado sem alterar Neon/Cloudflare de produção, checar isolamento de roles e orçamento zero. Depois, com lease nova, promover somente uma rota por vez; proibir CI redundante e publicação concorrente.
5. Confirmar custo/quotas do provedor; Vercel HTTP 402 permanece WAITING_EXTERNAL, com alternativa Cloudflare/Neon já autorizada, não homologada como publicador final.
6. Executar testes Python em runner hospedado autorizado após conferência de quotas, evitando testes repetidos sem nova causa.

## Rollback / estado
Nenhuma mudança de produção nesta lease. Reverter duas branches/fechar PRs isoladas se a revisão rejeitar. Os 68 UNCERTAIN e dados privados permanecem intactos. A lease da área queue está ENCERRADA com este finding; nova alteração de produção exige lease e SHA atualizado.
