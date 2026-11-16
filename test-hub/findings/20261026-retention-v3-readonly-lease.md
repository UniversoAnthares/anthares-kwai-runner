# RET-02/04 — lease: auditoria criptográfica de proveniência somente leitura
STATUS: RUNNING
AREA: retention
DATE: 2026-10-26
RUN: none
JOB: RETENTION-V3-READONLY-20261026
COMMIT: base anthares-kwai-runner 513c8f4015a1c40c7a070f1648b1bb136e163e58
SUPERSEDES: none

## Escopo e propriedade
Owner: ChatGPT / Universo Anthares. Lease apenas para criar código e testes isolados de QA em branch dedicada de anthares-clipper, sem execução produtiva. Expiração máxima: 30 minutos após a criação deste finding. Não persistir exclusividade além desse limite.

## BASELINE_PROVEN
Governança main manifest.version=f6fc9ca59a96e451 conferida; Windows policy.py preflight RETENTION-QA-20261026-REVALIDATE retornou sucesso. Contrato F1 vigente: duas cópias e preservação do original. Pacote v2 local: 26 testes sintéticos de avaliação/proveniência, sem upload e sem exclusão.

## FAILED_AVOIDED
Upload rclone por WinRemote e criação de pasta Google Drive anteriormente recusados expressamente pela camada de segurança. Não repetir nem substituir por outra ferramenta. Auditoria Windows ampliada teve recusa; nenhuma operação equivalente está neste escopo. Registro atual é trabalho independente de código QA sem qualquer transferência.

## SUCCESS_SIGNAL
Nova suíte offline QA somente leitura com assinatura Ed25519 de receipts, escopo de chave por conta, revogação, hash, prevenção de receipt falso e reconciliação do inventário histórico. Códigos e testes publicados em branch isolada, sem modificar main, sem deploy, com hash/commit verificável.

## FAILURE_SIGNAL
Escrita recusada ou lease/HEAD divergente, falha de teste, segredo exposto, seleção de arquivo fora do escopo, qualquer mutação de Drive/Windows ou tentativa de modificar F1 vigente.

## TEST_VALIDITY
Testes sintéticos nunca serão descritos como prova de origem real de arquivos nem de backup/restauração. Pacote de inventário real apenas read-only; SHA remota não validada.

## Guardas
Nenhum segredo, cookie, client_id, token ou token de runner. Proibido criar upload, delete, move, limpeza agendada, alterar F1, filas e mídias. Qualquer conflito de lease interrompe este trabalho. Encerrar com finding append-only e evidência.