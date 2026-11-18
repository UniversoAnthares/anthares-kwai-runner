# Studio — hotfix em produção e reconciliador de alterações simultâneas
STATUS: PARTIAL
AREA: anthares-studio/production/parity
DATE: 2026-11-18
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-parity-20261118
SOURCE: https://github.com/UniversoAnthares/anthares-wordpress/pull/326
SUPERSEDES: test-hub/findings/20261118-studio-trash-retention-qa-proven.md

## Aplicação verificada na Hostinger
- Corrigida representação de retenção da Lixeira com flag verdadeira `trashCleanupEnabled` injetada pelo PHP e mensagens condicionais no JS, sem mudar dados, autorizações ou agendamentos.
- Plugin novo ativo `0.7.8-staging`; PHP sintaxe PASS e teste de isolamento instalado 8/8 PASS.
- PHP de produção SHA256 `36b83bf049767d60b8fe4e9345e312f8423ab80818ef83e8ce98e408e7c9f9e0`.
- JS inicialmente instalado a partir da PR SHA256 `0bac87e88c65f49b067e9768329ad13bb71559f59af591f941e7b9924b9cc11c`.
- Backup privado do estado anterior: `/home/u566597497/domains/anthares.us/anthares-private-storage/studio-ui-hotfix-20261118T130356Z/` (previous.php e previous.js; diretório de modo 0700).
- PHP original `/estudio` preserva SHA256 `13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf`.
- REST anônimo: GET `/anthares-estudio/v1/bootstrap`, `/anthares-studio/v1/bootstrap` e `/anthares-studio/v1/trash` responderam HTTP 401; nenhum POST realizado.

## Convergência e concorrência
- Outra alteração de JS da Hostinger às 13:06Z mudou SHA256 para `602fc0cd901f2d0e74a8751dd06c8c8a63bfd766827f706ae3e648af4b57c86f`.
- A versão mais recente ainda contém `cfg.trashCleanupEnabled` e inclui `view==='lixeira'` na indicação do grupo Meus projetos.
- Respeitar o estado mais recente; NÃO sobrescrever cegamente o JS. PR #326 permanece draft, com QA 92/92 para a branch.
- O navegador pessoal possui as duas abas abertas, mas o conector de conteúdo devolveu falta de permissão da extensão para anthares.us. Não contornar essa restrição.

## Pendências
Comparação interativa autenticada controle a controle; restauração E2E de edição; homologação de acesso pago/ACF; autorização de merge e correção de divergências posteriores.