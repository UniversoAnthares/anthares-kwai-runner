# Kwai: correção das janelas 06h–23h implantada na Neon de produção

STATUS: DEPLOYED_AND_READONLY_HEALTH_VERIFIED; NO_POSTING_EXECUTOR_TEST
DATE_UTC: 2026-11-13
OWNER_SCOPE: Universo Anthares / Neon Functions / CORTES

## Causa
O diagnóstico anterior de que `cortesqueue` não estava acessível no conector Neon era incorreto: a branch principal do projeto conectado `anthares-ara-ha` hospeda a função. O código de pacing só bloqueava a partir de 23h e aceitava primeiro lease após meia-noite. A função ainda aceitava START de leases antigos sem cerca temporal atômica.

## Correções versionadas
- PR #2581: `deriveKwaiPacing` v3 inclui `window_open_at` a partir de 06h MS e retorna `WAIT_OPEN` até o horário; as duas rotas de lease usam apenas `DUE`. Fim exclusivo às 23h.
- PR #2582: reparo da asserção de teste restrita às duas rotas Kwai.
- PR #2583: as duas transições `kwai-start` exigem `(now() AT TIME ZONE 'America/Campo_Grande')::time >= time '06:00'` e `< time '23:00'` dentro do mesmo UPDATE com CAS do lease. Fencing de geração/owner, disponibilidade e prova de confirmação permanecem.
- PR #2580: identidade cloud secundária passa pelo gate, sem ativar produção. Oracle, CutMotions, GitHub Android experimental e infraestrutura paga permanecem excluídos.

## Ambientes, dados e prova
- Projeto: `purple-flower-35918989` (`anthares-ara-ha`), branch produção `br-crimson-unit-b89nau08`, branch QA `br-silent-mud-b8fzvqta`.
- Antes: produção `cortesqueue` deployment **73**, concluído 12/11/2026. QA **7**.
- Fonte do deploy: GitHub main com blobs
  `index.mjs=854312d6ef9edab923b21275d2ff6047803828ed`;
  `kwai-pacing-policy.mjs=957fb4406964523fe6ffb047172a5ac53451761f`;
  `kwai-persistent-cloud-identity.mjs=0004b2611fa6782f2222a3b39dc4559db75f6463`.
  ZIP determinístico com os três módulos, 182487 bytes, sem credenciais.
- QA: `cortesqueue` deployment **8** completed/active, GET `?action=health` `ok=true`, `database_ok=true`.
- Produção: mesmo conteúdo fonte aplicado com Neon `deploy_function`, ambiente preservado por omissão de `environment`. `cortesqueue` deployment **74** completed/active em 2026-11-13T21:09:55.900424Z. GET `https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/?action=health` retornou `ok=true`, `database_ok=true`, backend `neon-functions-cortes`.
- Gate CI: workflow `Kwai proporcional até 23h - invariantes`, run `43507771126` passou antes do ajuste do SQL de START; alterações subsequentes para START testadas no PR #2583 e Actions run da sua main. QA e produção mantiveram o banco e as variáveis existentes.

## Comparativo de estados com SELECT (antes e depois idênticos)
| Conta | confirmed | queued | started | uncertain | failed | cancelled |
|---|---:|---:|---:|---:|---:|---:|
| `kwai:lucasrosalem` | 606 | 16 | 0 | 2 | 14 | 2 |
| `kwai:universoanthares` | 47 | 52 | 1 | 0 | 1 | 5 |

Nenhum `kwai-lease`, `kwai-start`, `kwai-confirm` nem publicação de vídeo foi invocado nesta alteração. Nenhum status de tarefa foi alterado, nenhum executor local removido ou cloud habilitado.

## Limites da prova
- O GET público `health` ainda reporta `network_isolation=false`, `rls_attested=false` e `isolation_status=UNPROVEN_SQL_ROLE_AND_RLS_SCOPE`: **isolamento SQL/RLS não comprovado**.
- `android_execution.cloud_cutover.enabled=false` permanece ativo no manifesto; `KWAI_PERSISTENT_CLOUD_PUBLISH_ENABLED` não foi habilitado, nem token/servidor criado.
- Prova de que o código de production está implantado e responde com health positivo. Prova **não inclui** um Kwai real publicado por cloud, teste de token de Android ou verificação de toda a lógica transacional com credenciais.
- Próximo trabalho sem custo novo: manter reconciliação read-only de started/uncertain e critérios de idempotência; jamais requeue uma publicação incerta sem prova independente. Migração Android sem PC/celular continua sem host viável e gratuito.

SUCCESS_SIGNAL: deployment 74 active + GET ok + database ok + state snapshot unchanged + 06/23 clauses in source + CI PASS.
FAILURE_SIGNAL: saúde da função degradada; cloud ativado sem provas; novo START fora da janela; row count inconsistente.
