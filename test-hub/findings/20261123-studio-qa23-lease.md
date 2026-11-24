# Lease do Test Hub — QA23 / Studio, 23/11/2026
STATUS: RUNNING
AREA: studio
DATE: 2026-11-23
OWNER: QA_STUDIO_23_24_20261123 / ChatGPT
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/421
JOB: none
COMMIT: 1bed3055b7cc1133377a667a2f3a9c5e4ace448e
SUPERSEDES: none

## Objetivo
Homologar itens 23 e 24 do backlog urgente do Anthares Studio; item 24 foi incorporado ao main via PR #421.

## Baseline e restrições
BASELINE_PROVEN: plugin de produção tem SHA-256 68/68 igual ao main 4ec1643f; testes REST de leitura, seis papéis e isolamento PASS; dados preservados 82 antes/depois.
FAILED_AVOIDED: CLI PHP 7.4 quebra; usar PHP 8.3 explícito. GET /projects e GET /notes não são endpoints; usar /bootstrap e /trash. Comparação de working-tree CRLF gera falso diff; usar git cat-file.
SUCCESS_SIGNAL: ensaios sintéticos sem divulgação de dados, cada execução com TOTAL_PASS, ROLLBACK=EXECUTED e conferência de contagem pós-teste.
SCOPE: apenas QA interno, sem pagamentos, posts públicos, webhooks, emails, mudanças de usuário, alteração em textos reais ou no /estudio antigo. Escrever exclusivamente fixtures sintéticos sob transação InnoDB e com rollback; interromper ante qualquer dúvida.
EXPIRES_UTC: 2026-11-24T02:00:00Z

## Evidências já obtidas
- QA23 papel REST seis perfis existentes: 6/6 coerentes; visitante 401 em 3 rotas privadas; descoberta 200.
- 120 rotas registradas no Studio; verificação de proprietário e outra conta PASS.
- 268 contratos: 255 PASS / 13 SKIP / 0 FAIL após atualizar contratos.
- 34 PHP lint PASS; 22 JS check PASS; 775 manifestos PASS.
- Homologação visual mobile, concorrência real, volume e compra ativa/expirada ainda PENDENTES.

## Protocolo
Ler QA e scripts completos antes de executá-los. Conservar logs exclusivamente de códigos/casos; interromper ante qualquer erro sem rollback. Encerrar com finding posterior append-only.
