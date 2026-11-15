# Anthares Studio / Agente 04 — migração de produção comprovada
STATUS: PROVEN
AREA: github
DATE: 2026-11-15
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/287
JOB: Hostinger WP-CLI + MariaDB isolado + QA integrado
COMMIT: 621dc2bb6c89442dde0707d6e01b71a947fd5169
SUPERSEDES: test-hub/findings/20261115-wordpress-studio-agent04-migration-preflight-partial.md

## Objetivo
Migrar todas as entidades publicadas do plugin antigo `aest_*` ao
novo `anst_*`, mantendo origem, histórico Quill Delta e dados
na lixeira, com backup integral, idempotência e rollback protegido.

## Resultado
- `execute` real: PASS, código 0, `completed=true`,
  40 registros copiados e publicados (17 projetos, 8 ideias,
  4 notas, 5 cartões, 6 capítulos); zero erros ou divergências.
- `verify` pós-migração: PASS, código 0, 40 registros
  `ALREADY_IMPORTED_VERIFIED`, zero pendências, zero divergências.
- Origem e lixeira: registros `aest_*` preservados;
  31 registros da lixeira permaneceram na origem.
- Checksum da origem: `4607b131043191ac2a6d74992cd76891201e84f07827fcdd674b06a59a73b236`,
  estável entre dry-run e verificação final.
- Run definitivo: `agent04-execute-20261115-1`.
  Checkpoint e evidências JSON retidos em área privada da hospedagem.

## Proteção e restauração
- Backup privativo do banco SQL.gz e do diretório completo de uploads
  (~15 GB). Hashes SHA-256 verificados pelo próprio importador.
- Banco restaurado em MariaDB 11.8 independente, com socket privado,
  rede desabilitada: 217 tabelas, 15.047 linhas wp_posts,
  61.717 wp_postmeta e 1.887 wp_options. Importação concluída com
  código 0. Processo MariaDB isolado encerrado após a prova.
- Arquivo de imagem extraído do TAR foi idêntico byte a byte
  ao original.
- Primeira `test-copy` detectou divergência no comportamento
  WordPress de post_modified; correção e regressões testadas, limpeza
  e recuperação verificadas. Segunda `test-copy` real:
  40 copiados, 40 removidos, zero erros.
- Backup da versão anterior do plugin ativo foi feito antes da instalação.

## QA e integração
- Manifestos de QA sincronizados, 665 caminhos auditáveis, 665
  atribuídos exatamente uma vez: PASS.
- QA orquestrador, ACF schema (12 grupos / 313 campos),
  ACF runtime, normalização, relações e importador PHP: PASS.
- /studio ativo em produção, novo grafo relacional instalado;
  rota HTTPS confirmou resposta HTTP 200.
- PR #287 mesclada à branch de integração do Studio (#275).
  Commit merge `621dc2bb6c89442dde0707d6e01b71a947fd5169`.
- Testes de JavaScript Node/SQLite e homologação visual completa
  continuam pertencendo aos responsáveis específicos do Studio.
