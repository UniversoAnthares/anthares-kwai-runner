# Lease — seção Leituras beta disponíveis
STATUS: RUNNING
AREA: wordpress-home-beta-opportunities
DATE: 2026-10-31
RUN: none
JOB: chatgpt-20261031-home-beta-opportunities
COMMIT: bed079bbf97c6351e15da290036460bfc2a96d48
SUPERSEDES: none

## Escopo e duração
Owner ChatGPT/GPT-6. Expiração máxima 30 minutos. Apenas `anthares-home` (catálogo, layout, elegibilidade, novo template e CSS) + `anthares-pix-sales/includes/65-leitura-beta.php` (regra de acesso role anthares ao fluxo de leitura) e os dois manifestos QA. Nenhum outro plugin/perfil alterado.

BASELINE_PROVEN: layout do Laboratório auto-completa novas seções; backend de leitura beta possui tabelas de ofertas e leituras, fluxo de leitores e reserva em Runas. Papel exato `anthares` já possui liberação para publicar ofertas, e nova seção deve permitir a leitura de ofertas de outros autores.
FAILED_AVOIDED: não duplicar fluxo de pagamentos nem movimentar Runas na Home; não escrever arquivos no PC, não acionar runner Windows, não criar contos/leituras reais em QA.
SUCCESS_SIGNAL: nova seção registrada e habilitada no layout padrão dos cinco perfis, visível somente para role `anthares`, cards com autor, título, vagas e Runas obtidos de dados reais, CTA para fluxo existente, estado vazio; QA manifest+PHP lint+contrato; WordPress produção correspondendo ao git, renderização confirmada com role.
FAILURE_SIGNAL: erro PHP/QA, oferta inválida, exibição a outro role, saldo modificado durante render, divergência de hashes ou malha do Laboratório quebrada.
TEST_VALIDITY: validação por leitura de HEAD e blob no destino; artefatos de testes temporários externos e removidos; sem dados financeiros reais gerados.
