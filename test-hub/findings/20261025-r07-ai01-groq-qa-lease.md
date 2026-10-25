# R07.6 item 27 AI-01 — lease: auditoria de upstream Groq em QA
STATUS: RUNNING
AREA: ai-audit
DATE: 2026-10-25
RUN: none
JOB: r07-ai01-groq-qa-20261025
COMMIT: branch isolated from 183f6a8eda4d2585f6cdd73982984a66df541802
SUPERSEDES: none

## Baseline e fronteira
BASELINE_PROVEN: Anthares AI Hub versionado referencia Groq modelo openai/gpt-oss-20b; documentação oficial Groq confirma JSON Object/Schema, preço nominal e métricas de quota. Governança preflight local f6fc9ca59a96e451 PASS, audit 218/0.
FAILED_AVOIDED: não repetir a consulta de autenticação local 9Router bloqueada por segurança em 2026-10-25. Não ler, transferir nem registrar segredos. Não alterar consumidor real, credenciais, filas, provedores, produção ou permissões.
SUCCESS_SIGNAL: código de auditoria fail-closed revisado, testes unitários aprovados, execução documentada; autenticação, quota e resposta real são campos independentes e, se indisponíveis, manter status PARCIAL.
FAILURE_SIGNAL: vazamento de chave, requisição sem autorização explícita, marcação de PROVEN sem resposta autenticada ou sem dados de quota da conta.
TEST_VALIDITY: fixture de HTTP estritamente sintético identificada; resultados sintéticos classificados QA, jamais como inferência de Groq real.
LEASE: escopo de criação de novos arquivos de auditoria em branch isolada, validade máxima 30 min. Não conflita com PR #1392 (AI-04) e não toca arquivos compartilhados.
