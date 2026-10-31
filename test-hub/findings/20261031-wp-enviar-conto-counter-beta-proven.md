# Correção de Enviar Conto — contador, botão Enviar e leitura beta
STATUS: PROVEN
AREA: wordpress-enviar-conto
DATE: 2026-10-31
RUN: Hostinger SSH / QA externo / simulação JS
JOB: chatgpt-20261031-enviar-conto
COMMIT: bed079bbf97c6351e15da290036460bfc2a96d48
SUPERSEDES: test-hub/findings/20261031-lease-wp-enviar-conto-form-fix.md

## Resultado
PR #212 e PR #213 mescladas em `UniversoAnthares/anthares-wordpress`. Modificação isolada no arquivo `anthares-pix-sales/includes/65-leitura-beta.php` para a página /enviar-conto/.
- Suporte ao TinyMCE assíncrono, contagem Unicode do texto e atualização do botão conforme 1000 a 2000 palavras, desafio, título, ranking e campo `anthares_analisar_live`.
- Botão de leitura beta com submissão independente da guarda do envio normal, sincronizando o editor.
- Expressão Unicode corrigida após simulação detectar escape duplicado.
- Simulação isolada da versão corrigida: 1100 palavras: Enviar habilitado; 650 e 2400: Enviar bloqueado; beta submit independente do limite (PASS).
- PHP 8.3 lint PASS; QA manifest 599/599; orquestrador QA PASS.
- Hostinger: `LIVE_GITHUB_BYTE_MATCH=yes`, `LIVE_VERIFIED=yes`, PHP lint PASS, versão `bed079bbf97c6351e15da290036460bfc2a96d48`; backup privado do módulo existente.
- Sem trabalho/arquivos no PC, sem postagem real de conto e sem transferência de Runas.

## Limite
A simulação JS e o teste de arquivo publicado comprovam correção do programa; execução interativa final num navegador logado com submissão de conto real não realizada para evitar alterar conteúdo do usuário. Testar a contagem após recarregamento completo da página e registrar regressão se persistir.

Lease encerrado.