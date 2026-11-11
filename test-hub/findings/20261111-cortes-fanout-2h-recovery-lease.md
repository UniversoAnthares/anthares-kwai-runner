# CORTES fanout — lease de recuperação de cobertura
STATUS: PARTIAL
AREA: cortes-fanout
DATE: 2026-11-11
OWNER: chatgpt-cortes-fanout-2h-20261111
LEASE_EXPIRES_UTC: 2026-11-11T21:00:00Z
LEASE_STATE: CLOSED_AFTER_BRANCH_COMMIT
SCOPE: .github/workflows/cortes-buffer-three-fanout-cloud.yml, tools/cortes_buffer_three_fanout.py, tests/test_three_network_fanout_daily.py
BASE_HEAD: ee1b1669f044f0045eddfb3f2ab43def6e161053
NO_SOCIAL_POSTS_FROM_THIS_CHANGE: true

## Motivo
A fonte corrente possui 229 segmentos previstos, enquanto o produtor de fanout cobre uma janela de ate 50 cortes por destino a cada seis horas e apenas tres disparos por dia. Isto deixa masters ja disponiveis fora da fila no proprio dia.

## Teste e evidência
- Cursor da rotação: para cinco janelas, os horários UTC 11,13,15,17,19 visitam 4,0,1,2,3, cobrindo os 229 masters.
- Para duas janelas, alterna 1,0,1,0,1, sem ignorar o segundo lote.
- Foram mantidos os testes de deduplicação, isolamento por rede e `diagnose_only`.
- Execução de QA read-only solicitada na branch: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43096168314; à data da anotação permanece QUEUED, sem prova CI positiva.
- Publicação existente, Buffer, cotas e Neon não foram mutados por esta alteração.

## Contrato
Distribuir as janelas em ciclos de 2 horas durante a janela editorial, preservando a identidade deterministica, CAS Neon, limites reais de Buffer e travas de publicador. O fanout apenas enfileira, nao comprova publicacao. Testes unitarios sinteticos antes do merge; verificar jobs e contagens reais sem reenvio incerto.
