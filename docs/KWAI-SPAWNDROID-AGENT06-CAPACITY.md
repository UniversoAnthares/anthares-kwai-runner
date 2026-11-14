# AGENTE 06 — admissão de capacidade do SpawnDroid (staging protegido)
Data: 2026-11-14. Branch isolada: `agent06/spawndroid-capacity-failclosed-20261114`.

## Estado comprovado
- GitHub main `5db0bf2...`: adaptador `tools/kwai_spawndroid_stable_hub.py` usa WebDriver para ativar um APK Kwai e confirmar teardown; não faz login ou publicação.
- Neon `cortesqueue` deployment 77, banco `anthares-ara-ha` ativo; fonte de pacing `infra/neon-cortes-queue/kwai-pacing-policy.mjs` define 06:00–23:00 no fuso America/Campo_Grande e quota máxima 100/conta. Publicadores Windows permanecem governados pelo seletor atual.
- `ci-hub/executor-routing.json`: `android_execution.cloud_cutover.enabled=false`. Esta branch não muda o seletor, o banco, as filas nem os jobs ativos.
- O runtime do SpawnDroid não foi homologado para login duplo, upload, prova independente ou persistência de sessão.

## Franquia real e cálculo conservador
Documentação oficial: https://docs.spawndroid.io/docs/plans/ (confirmada em 14/11/2026). Hobby: R$0, 200 device-minutes/mês, 1 dispositivo concorrente, sessão máxima 15 min, idle 3 min, encerramento duro ao esgotar franquia. Minutos começam em device-ready; provisioning anterior não conta. O orçamento pertence à pessoa, inclusive entre workspaces Hobby; por isso o controle deve consumir uso/reservas de *todos* os workspaces.

**Atenção:** resumos indexados do provedor podem mostrar franquias divergentes; o limite conservador operacional permanece fixado em 200 até autenticação atual e revisão controlada. Nenhuma hipótese aumenta essa franquia automaticamente.

Um teto de 100 posts/dia em **cada** conta equivale a 6.000 posts em 30 dias. 200 minutos de franquia exigiriam custo médio máximo de **2 segundos de dispositivo por post**, incluindo app, autenticação, MP4, postagem, verificação, falhas e teardown. A franquia por si só, sem medição, não autoriza essa meta.

O contrato `tools/kwai_spawndroid_admission.py` aceita somente:
1. Snapshot autenticado recente (até 120 segundos) do Hobby, com limite 200, 1 slot, cobrança por excedente desativada, uso acumulado e reserva para sessões concorrentes. `source` em JSON é um rótulo de transporte, **não** uma assinatura; cabe ao adaptador privilegiado validar que os campos vieram do provedor.
2. Pelo menos três sessões completas **reais e independentes por conta**, cada qual com ID de sessão único, URL pública de vídeo da conta correta, identificação de leitura independente, estado `closed` confirmado e timestamps com fuso em ordem crescente: solicitação; device ready; ativação do app; autenticação; MP4 carregado; publicação; prova pública; dispositivo encerrado.
3. Snapshot Neon autenticado recente por conta com fila, consumo do limite diário, relógio da última publicação pública, itens `started/uncertain` pendentes e teto configurado (1–100).
4. Multiplicador de reserva para falhas de pelo menos 1,25 e espaçamento mínimo de ao menos 60 segundos; o valor de produção deverá ser escolhido com base em latência medida e regras do Kwai.

Usa P95 *por conta*, reserva de falhas, arredondamento conservador de minutos por sessão e maior custo entre as contas para estimar o teto **compartilhado**. Divide a capacidade mensal remanescente pelos dias restantes para um ritmo sustentável. Planeja somente dentro de 06:00–23:00, com cutoff exclusivo e intervalo mínimo. A função Neon continua sendo autoridade de relógio e lease: o planejador offline não cria jobs.

Exemplo de cálculo (dados **sintéticos** do teste): sessões de 160 s após device-ready e reserva de 25% = 4 minutos reservados por vídeo. Se as duas contas mantivessem esse P95, 200 min permitiriam no máximo 50 posts durante o mês, divididos entre as duas. Substitua exclusivamente por evidências remotas reais.

## Quotas e recuperação
`quota_cancel_disposition` valida a máquina de estados de decisão. HTTP 402 confirmado deve acionar **chamada real de cancelamento** no adaptador que detém o ID da sessão, seguida de readback de estado terminal. Sem confirmação: `CANCEL_UNCONFIRMED`. Efeito Kwai desconhecido: `RECONCILE_REQUIRED`. Efeito comprovadamente `NOT_APPLIED`, sem reserva independente: `CANCELLED_NO_INDEPENDENT_RESERVE` e corte permanece na fila. HTTP 429 é falta de slot concorrente, e 401/403 indicam autenticação/permissão: não tratar como quota e não contornar controles.

Esta branch instala **somente a regra de decisão offline**; o cancelamento real via WebDriver/REST, readback terminal, liberação de lease e migração governada dependem do adaptador operacional e da prova dos agentes 01–05. Nunca interpretar a rotina de decisão como cancelamento executado.

## Integrações bloqueadas até comprovação
- AGENTE 01: APK oficial cadastrado e integridade real do Kwai e Kwai Lite.
- AGENTE 02: início/encerramento reais, ID de sessão, limite ativo e timestamps provenientes do SpawnDroid.
- AGENTES 03/04: identidade autenticada, MP4, publicação e prova pública independente em cada conta.
- AGENTE 05: autenticação repetível sem transferência ilegítima de sessão entre contêineres descartáveis.
- AGENTE 06: adaptar recibos medidos ao controle autenticado, reservar capacidade antes do lease, garantir exclusão global entre publicadores, integrar cancel/status/teardown reais e validar operador sem PC.
- Test Hub: registrar todas as medições e a conta, vídeo, horários, consumo e run ID, sem credenciais. Nunca fazer canário de publicação apenas para auditar código.

## Barreira de produção
`evaluate()` retorna sempre `production_eligible=false` e `cloud_cutover_enabled=false`. CI usa apenas fixtures sintéticas e verifica as recusas. Mesmo com CI verde, nenhum controlador pode habilitar a produção por meio desta biblioteca. O corte exige o contrato de `docs/KWAI-CLOUD-CUTOVER-CONTRACT.md`, revisão de lease de migração, prova remota, cancelamento efetivo, reconciliação e rollback.

**Reversão:** enquanto a PR estiver em draft, bastará não incorporá-la; não houve qualquer mudança de serviços. A implementação usa somente GitHub-hosted CI, sem PC, credenciais, vídeos ou sessão do SpawnDroid.
