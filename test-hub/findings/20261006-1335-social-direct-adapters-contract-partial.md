# Social direct adapters — contract proven
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37470378653
JOB: 112292004389
COMMIT: 22c59c2e2fe1bd854416ba1cdf2378e51a96150d
SUPERSEDES: none

## Objetivo
Fechar a camada independente de adaptadores para instagram:primary, threads:primary e x:primary sobre o destination_key PROVEN.

## Resultado
Contrato automatizado passou. Instagram e Threads implementam auth gate, criação/publicação via API oficial e verificação do remote_id antes de CONFIRMED. X oficial permanece fail-closed por padrão porque a rota de escrita é paga; só habilita com X_ALLOW_PAID_API=1. account_id permanece isolado no destination_key.

## Evidência decisiva
Run 37470378653 / job 112292004389: step Fail-closed adapter contract = success.

## Bloqueio atual
Instagram/Threads: credenciais/app OAuth Meta ainda ausentes; estado operacional AUTH_REQUIRED até autorização da conta. X: custo da API oficial exige opt-in explícito; automação web gratuita ainda não foi provada.

## Consequência
Preservar social_adapters/direct_social.py. Próximo agente pode fechar Meta criando/autorizando o app e fornecendo os tokens via secret store, sem gravá-los no Hub. Para X, preferir rota gratuita/browser separada; jamais ativar X_ALLOW_PAID_API implicitamente. Nenhum desses adaptadores deve concluir delivery sem remote_id + confirmation_evidence.

## Lease
Lease 20261006-1325 encerrado nesta camada; publicação real continua pendente dos gates externos acima.
