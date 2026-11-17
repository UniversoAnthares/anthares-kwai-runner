# Studio G4 PR316 — QA de código isolada, independente do lease de escrita G4

STATUS: RUNNING
DATE: 2026-11-17
AREA: anthares-studio/g4/independent-static-qa
JOB: studio-g4-pr316-readonly-code-qa-20261117
OWNER: ChatGPT / OBSERVATORIO IPB
SOURCE: UniversoAnthares/anthares-wordpress PR #316 HEAD cc9f0d07cb7e4d2338d4da9b640c901b88ffe74c, validada por GitHub e git ls-remote origin.
PEER: GitLab branch PR316 não verificada no commit atual, sem ação no GitLab.
BASELINE_PROVEN: PR #317 G5 58/58 Python, 4 PHP lint, 665/665 preflight e 11/11 orquestrador em clone efêmero Hostinger; ambiente de teste privado autorizado; sem produção.
FAILED_AVOIDED: não executar CRUD/REST mutações nem acessar aba autenticada após bloqueios explícitos da ferramenta.
SCOPE: clone efêmero em Hostinger + Python unittest, PHP lint e manifesto QA; somente leitura do código da PR316; não alterar o código sob lease G4 de outra frente, nem os dados reais.
SUCCESS_SIGNAL: resultados e commit exato registrados, limpeza de clone comprovada.
FAILURE_SIGNAL: registrar erros como defeitos da suíte/code sem reinterpretar como falha de produção; nenhuma repetição sem correção causal.
TEST_VALIDITY: suíte do commit isolado; não comprova cliques, salvamento REST nem paridade visual.
ROLLBACK: limpeza automática do clone temporário em trap EXIT.
