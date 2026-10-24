# Lease — reconciliação pública de 1 LinkedIn personal incerto
STATUS: RUNNING
AREA: linkedin
DATE: 2026-10-24
RUN: pending GitHub Actions
JOB: CORTES LinkedIn personal reconcile-only
COMMIT: 11b8d69d4d015ab746932cbf0f784200c348852e
SUPERSEDES: none
LEASE_AREA: linkedin-personal-external-proof-readback
LEASE_OWNER: ChatGPT current conversation
LEASE_START_UTC: 2026-10-24T17:55:00Z
LEASE_MAX_EXPIRY_UTC: 2026-10-24T18:25:00Z

## Objetivo
Concluir a reconciliação do post LinkedIn personal id urn:li:ugcPost:7519814015376584704, com prova pública independente de embed HTTP 200 e controle inexistente 404. Não criar post nem reenviar mídia.

## BASELINE_PROVEN
Ledger Neon purple-flower-35918989, public.cortes_publications: id cortes-fanout-linkedin-ab26eee71e88fca5f1d079cb6dec52db, status uncertain, remote_id presente, kind linkedin_api_201_unverified. TinyFish GET público do embed exibe autoria e vídeo esperado; controle remoto inexistente retorna 404. GitHub main SHA 11b8d69d4d015ab746932cbf0f784200c348852e. Workflow existente .github/workflows/cortes-linkedin-personal-cloud.yml, blob 7e127225871bd30eecc77f5915bb8a5b8db4401f, aceita workflow_dispatch input reconcile_only=true e seu step de publish tem exclusão expressa desse modo. Script tools/cortes_linkedin_personal_cloud.py, SHA 1243f006293925af4cebdd185f8b5a3bdcdef859, função reconcile_personal() com account_preflight, HEAD público 200 e controle 404, OIDC e CAS da fila; não faz upload. Peer GitLab duo-main não tem esse workflow (404); preservar histories e não espelhar por inferência.

## FAILED_AVOIDED
Nenhuma publicação, upload, teste E2E mutante, token exposto, GET de handoff Threads anteriormente negado, operação Windows ou bypass de controle de segurança. Não atualizar Neon por SQL direto; somente caminho canônico autenticado. Um disparo de workflow exclusivamente reconcile_only, sem código de rede acionado a partir do novo dispatcher (somente gh workflow run). Conferir identidade, evidência e CAS após o run; nenhum replay cego.

## SUCCESS_SIGNAL
GitHub Actions one-shot dispatch concluído, canonical workflow_dispatch reconcile_only=true concluiu sem etapa de publish; saída PERSONAL_READBACK_ONLY_RECONCILED>0; o único registro alvo no ledger mudou uncertain -> confirmed com evidence.kind=linkedin_public_embed_http200 e remote_id idêntico; controle negativo 404. Nenhum novo post enviado.

## FAILURE_SIGNAL
Disparo não executado, conta OAuth errada, Bitwarden/token indisponível, HEAD público não reproduz 200/404, estado stale no CAS, publisher executado por engano ou run iniciado sem reconcile_only. Em qualquer dessas situações deixar o ledger untouched e reportar sem repetir publicação.

## TEST_VALIDITY
GET público não confere automaticamente CAS. GH dispatch ACK não prova reconciliação nem publicação. Estado final só é aceito após leitura Neon e logs de job; workflow deve ser removido/neutralizado após o disparo único. Caso concorrente já confirme o mesmo registro, classificar CAS stale como reconciliação externa verificada e não duplicar trabalho.

## Consequência
Lease temporário; ao finalizar escrever finding append-only com SUPERSEDES. Nunca transformar modo reconcile_only em modo publish.
