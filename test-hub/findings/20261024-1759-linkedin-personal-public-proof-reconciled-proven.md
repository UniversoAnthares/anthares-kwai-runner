# CORTES LinkedIn pessoal — reconciliação pública efetiva, sem novo upload
STATUS: PROVEN
AREA: linkedin
DATE: 2026-10-24
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40118552924
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40118552924/job/120944924039
COMMIT: 11ab3360f6b992287df3618f0cd680ef2b04292d
SUPERSEDES: test-hub/findings/20261024-1757-lease-linkedin-personal-reconcile-once.md
LEASE_AREA: linkedin-personal-external-proof-readback
LEASE_STATUS: CLOSED

## Objetivo
Resolver uma publicação LinkedIn personal accepted/uncertain com identificador remoto verificável, usando somente o caminho canônico existente reconcile_only=true, sem postar outro vídeo.

## BASELINE_PROVEN
Neon public.cortes_publications na branch principal: id cortes-fanout-linkedin-ab26eee71e88fca5f1d079cb6dec52db, target_key linkedin:personal, status uncertain, remote_id urn:li:ugcPost:7519814015376584704, evidência linkedin_api_201_unverified. A incorporação pública https://www.linkedin.com/embed/feed/update/urn:li:ugcPost:7519814015376584704 exibiu autoria e vídeo esperado. Controle negativo urn:li:ugcPost:1000000000000000000 teve HTTP 404; a rotina canônica exige HEAD 200/controle 404 novamente sob GitHub Actions OIDC e validação OAuth da conta. Outro agente não possuía lease LinkedIn ativo na inspeção prévia. Peer GitLab divergia sem esse workflow; nenhuma sincronização cega foi feita.

## FAILED_AVOIDED
Não usar Windows remoto cuja leitura fora negada, nem consulta vedada do handoff Threads. Não fazer INSERT nem UPDATE manual no ledger, reenviar vídeo, acionar publisher ou copiar tokens. Gatilho temporário com permissões actions:write e contents:read chamou APENAS o workflow existente cortes-linkedin-personal-cloud.yml com input booleano reconcile_only=true. A etapa publish_one era negada explicitamente nesse modo, independentemente do estado de saúde do primário. Sem nova mídia.

## SUCCESS_SIGNAL
PR #1318 integrou dispatcher estreito e lease em merge 97c16feb981f83fc0bea424e795da9069f7d8e59; PR #1319 integrou marcador único em merge 11ab3360f6b992287df3618f0cd680ef2b04292d. Disparador GitHub Actions run 40118547400 criou workflow_dispatch canônico run 40118552924, concluído success. Job 120944924039 executou Bitwarden scoped secret read, account_preflight e step de reconciliação, com linha decisiva PERSONAL_READBACK_ONLY_RECONCILED=1. Publicação foi excluída no workflow. Readback Neon pós-run confirmou status=confirmed, remote_id idêntico e confirmation_evidence.kind=linkedin_public_embed_http200, public_embed_status=200, control_embed_status=404, permalink canônico e updated_at 2026-10-24T17:58:40Z. Não houve novo upload.
A auditoria global do ledger antes da reconciliação continha 37 uncertain; a transição de um caso específico permite concluir 1 sem requeue e manter 36 restantes para verificação externa individual.

## FAILURE_SIGNAL
Se o estado tivesse permanecido uncertain, workflow não concluído, identidade diferente, HEAD de controle ambíguo ou publicação nova, seria FAILED/NOT_TESTED. Nenhuma dessas condições foi observada no run de reconciliação.

## TEST_VALIDITY
PROVEN para o caso EXATO LinkedIn personal com ID e remote_id acima. Não prova confirmação dos demais uncertain, isolamento de escritores globais, RLS produtiva, atestação editorial de mídia ou canário novo. Nenhum estado de outros registros foi alterado por esta operação.
A PR de fechamento remove dispatcher e marcador para impedir gatilho futuro; o finding é preservado no Test Hub.

## Consequência
Lease CLOSED. Não reenviar a publicação já confirmada. Não promover testes sintéticos ou Buffer IDs de agendamento como prova de publicação. Para cada novo uncertain, exigir prova externa específica e CAS nativo; nenhuma mutação por SQL manual.
