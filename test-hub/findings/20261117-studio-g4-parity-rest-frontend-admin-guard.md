# Anthares Studio — comparacao funcional e protecao piloto G4
STATUS: PARTIAL
AREA: wordpress/studio/g4-frontend-parity
DATE: 2026-11-17
RUN: Anthares Remote, WP-CLI somente leitura e auditoria GitHub
JOB: studio-g4-private-admin-write-20261117
COMMIT: ff05cd0dad8a9c19cd9a5df27abd53c4ae63c71e
PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/316
SUPERSEDES: none

## Evidencias verificadas em instalacao atual
- Navegador autenticado em /studio/#studio/inicio: UI apresenta 423, "O Estudio esta em homologacao somente para leitura."
- `anst_writes_enabled=0`, `anst_acf_runtime_enabled=0`.
- CPTs originais AEST e copiados ANST: 71/71, com 31/31 na lixeira.
- Chaves de proveniencia: 71 copias com origem valida, zero divergencias de titulo, proprietario, tipo e status.
- Quill: 7/7 Deltas idênticos por SHA-256.
- Bootstrap REST (mesmos dois proprietarios): source e clone HTTP 200, contagens identicas por proprietario para projetos/notas/capitulos/cartoes.
- Rotas REST comparadas na instalacao WordPress: 28/28, sem rotas ausentes ou extras.
- Comparacao dos JS source snapshot bruto G2 e novo G6: os 14 data-action literais presentes na origem permanecem no clone, sem exclusoes; nenhuma funcao nomeada da origem foi removida. A reorganizacao G6 acrescenta funcoes de navegacao interna.
- Manifesto GitHub na branch da correcao: 665 caminhos auditaveis, 665 atribuicoes, sem ausentes, duplicados ou extras; dois manifestos iguais.

## Codigo preparado
- Branch `fix/studio-g4-admin-write-guard-20261117`, PR #316 DRAFT.
- Mantem gate geral OFF por padrao; nova opcao `anst_pilot_admin_only` default 1 limita gravacoes aos administradores quando a flag geral for ativada em piloto aprovado.
- Teste estatico de permissao e fixture de verificacao dinamica sem mutacoes foram adicionados a testes existentes.
- Teste de regressao front-end verifica os mesmos 14 comandos de acao, controles de manuscrito, revisao e planejamento.

## Bloqueadores
- A PR foi criada **sem implantacao**. PHP lint/execucao de unit tests na versao final e a fixture dinamica em MariaDB isolado permanecem pendentes; nenhuma execucao verde deve ser inventada.
- A tentativa de clonar branch para QA por um canal remoto foi bloqueada pelas configuracoes de seguranca; nao alternar canais para contornar o bloqueio.
- Prova visual autenticada comparativa desktop/mobile (G4 C005-C008, C023) e o backup/restauro devem anteceder liberar gravacoes.
- Nao foi alterada qualquer opcao, arquivo ou dado da producao nesta rodada.
- Para habilitar o piloto apos QA e deploy seguro: preservar `anst_acf_runtime_enabled=0`, `anst_pilot_admin_only=1`; liberar `anst_writes_enabled=1` so apos backup testado e revisao de autorizacoes.
