# Anthares Studio: G5 ACF e G7 narrativo implantados
STATUS: PARTIAL
DATE: 2026-11-17
AREA: anthares-studio/production/g5-g7
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: anst-g5-g7-20261117
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/321
COMMIT: f0047f8dc6c1d2913c7af72964c898392a4ee9c7
SUPERSEDES: test-hub/findings/20261117-studio-acf-completion-lease.md;test-hub/findings/20261117-studio-g7-functional-integration-lease.md

## Entrega efetiva
- G5 migrador WP-CLI: source 71 posts / 413 metadados, fingerprint original 395eb2d6be445121283d9fd92735f5e86f7239743165f9197eb9312242f1c488; alvos ACF presentes passaram de 414 para 415, total esperado 413+1 zoom+1 options; 0 erros de referência. O comando de aplicação teve resposta de controle remoto inconclusiva; completude de presença confirmada em leitura posterior. Runtime ACF ativado (opção anst_acf_runtime_enabled=1 e aprovação mu-plugin externa).
- G7: merge nativo de Git entre PR #321 e PR #318, conflito JS resolvido preservando o bloqueio contra perda de Delta Quill e incorporando exportação TXT. Merge commit f0047f8. JS completo analisado em V8 (PASS), PHP do plugin e módulo de domínio sintaticamente válidos.
- Hostinger: plugin novo anthares-studio recebeu PHP, JS, domínio story e grupos ACF G7; PHP instalado SHA-256 e1c15b4b935ac2e498c70ba842423537fe9b96d49d73c1f82d9023c295c57e22; arquivo de domínio presente. Guard de implantação usou cópia de reversão em /home/u566597497/.anthares-studio-rollback/g7-20261118 e rollback em caso de falha. As cinco rotas de entidade/relação/curvas foram incluídas; retorno autenticado via navegador não testado.
- Preservados o plugin antigo /estudio, a autorização escrita individual do usuário 106, e o caráter privado dos dados.
- Diretório temporário /tmp/anst-g7-integration-20261117 removido ao final; nenhuma operação visível no desktop.

## Limite e fechamento
Resultado parcial: código G5/G7 implantado, mas 188 requisitos do curso não integralmente implementados. Não afirmar homologação REST autenticada/UI e G8; restrições prévias de segurança para essas superfícies foram respeitadas.
Leases G5 e G7 encerrados. Novas mutações exigem coordenação nova.
