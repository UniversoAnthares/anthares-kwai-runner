# Anthares Studio — G5 ACF runtime em produção e estado real de G4/G6
STATUS: G5_RUNTIME_PROVEN; G6_DEPLOYED_AND_SYNTHETIC_VISUAL_PROVEN; G4_PARTIAL
DATE: 2026-11-17 / America/Campo_Grande
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
SOURCE_PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/314 (DRAFT)
DEPLOY_TARGET: anthares.us/wp-content/plugins/anthares-studio (apenas cópia)
LEGACY: anthares-estudio preservado, sha256 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf
G5_PHP_BLOB: 16f5c01457085e73fcde291717ba46ebdbdb2801

## Evidências independentes
1. https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44008570966 — G4/G5/G6 código integrado com quatro blobs exatos; 48 testes; PHP lint; runtime G5 sobre MariaDB isolado, ACF OFF/ON, aplicação inicial e repetição, 2 autores, Quill, lixeira e permissão. Sem escrita na produção.
2. https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44014174931 — G4 visual em WordPress + MariaDB Docker temporários: 12 combinações (0/1/N projetos × desktop/mobile × claro/escuro), pares com largura proporcional 1.000, sem sidebar/título WordPress ou scroll horizontal inesperado. 25 screenshots sintéticas. G6 com 5 entradas globais e 7 grupos internos testados em navegador mediante clique; PASS. Containers removidos.
3. https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44014789855 — Código G6 e ACF implantado no novo plugin: 17 arquivos alterados, backup de código studio-g4g5-g6-backup-20261117T040625Z, REST/WordPress hashes e 71 registros verificados, escrita OFF, CSS G6 HTTP 200.
4. https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44081433713 — Backup integral studio-g1-backup-20261116-1527 verificado: dump + original tar SHA256 + RESTORE=PASS; 12 grupos ACF offline; manifesto SHA git b7b7b52b990279adb5cc8f5308c6cbedf1a4b325; registros AEST/ANST 71/71 e opções writes/cleanup/acf_runtime inicialmente 0.
5. https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44081609074 — WP-CLI dry run ACF live: source 71, source_meta 412, ACF targets 412 e existentes 414, user zoom 1, course option JSON 2 bytes, referência inválida 0, fingerprint bced1ad06c27a43a25585d9663457dd2cdc2f4c58f24bb1dada8696defe10bd1.
6. https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44082014104 — Comparação read-only 414/414 ACF já existentes com histórico: 412 postmeta, 1 zoom, 1 curso, 7 Quill Delta; SHA de cada valor e referência ACF; ZERO divergência. A cópia ACF estava previamente populada por outro executor, esta execução certificou sem regravar.
7. https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44083504490 — Diferença exclusiva de duas linhas de aprovação no PHP ativo reconciliada com o blob Git 16f5c0...; backup studio-g5-approval-code-backup-20261117T122901Z; canário modo ACF ON somente na memória do processo: 412 campos, 7 Delta, bootstrap de 2 autores idêntico ao legado, 12 grupos, 0 diferenças. Opção persistente mantida OFF nesta etapa.
8. https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44084091092 — Ativação PERSISTENTE controlada da opção anst_acf_runtime_enabled=1 em produção. Verifica antes/depois: backup restore, fingerprint, 414 ACF, 71/71, bootstrap de dois autores ACF OFF vs ON com hashes idênticos, 12 grupos registrados, writes=OFF, cleanup=OFF, plugin original imutável. Reversão automática preparada. Sucesso G5_ACF_PRODUCTION_ACTIVATION_PROVEN=1. Backup da opção studio-g5-option-rollback-20261117T123246Z.
9. HTTP rede em 17/11 12:34 UTC: assets/studio-g6-navigation.css 200, assets/estudio.js 200, /wp-json/anthares-studio/v1/bootstrap anônimo 401 (esperado), /studio anônimo 404 (página privada) e /estudio anônimo 200. Nenhuma rota privada ou payload de autores foi revelado pelo teste.

## G4 / Matriz C001-C025
Cobertura comprovada: C001/C002 isolamento original/clone e hashes, C003/4 instalação das páginas com controles, C005 equivalência básica de CSS/largura, C006/7 navegação global/interna (G6 após G4), C009/10/11/14/15/19/20/24 por testes de CRUD, Quill, lixeira e owners em banco isolado registrados na PR #310 e PR #311. C025 verificação parcial 401 REST e 404 página privada.
Restam sem homologação específica exaustiva: C008 reload/back/forward e estado de rolagem; C012 pastas/atributos/versões; C013 todas etapas de desbloqueio; C016 autosave após fechar e abrir; C017 histórico completo e restauração; C018 revisão/comentários; C021 matriz completa de erros 401/403/409/413/500; C022 concorrência em dois navegadores; C023 modais, Quill e drag mobile; C025 cabeçalhos cache/auth e HTML efetivo em produção. Além disso, screenshots de produção autenticada devem ser comparados ao cenário Docker; a navegação autenticada no live não foi observada por browser controlado nesta sessão.
**Portanto G4 permanece PARTIAL** apesar da equivalência visual de base aprovada; não registrar C001-C025 como all-pass por inferência.

## Controles e estado final
- /studio: privado; ANST_ACF_RUNTIME_APPROVED=true no novo PHP e anst_acf_runtime_enabled=1 no WordPress.
- 12 grupos JSON seguem com active=false no disco, sendo registrados ativos em memória quando runtime ACF ON (ACF Free). Manifesto idêntico ao validado.
- 414 campos convertidos previamente e confrontados byte a byte; _anst_* histórico retido. 71/71 posts, 7 Deltas e dois proprietários preservados.
- anst_writes_enabled=0, anst_trash_cleanup_enabled=0. Nenhuma criação/edição dos 71 posts reais feita nos testes.
- Reversão runtime ACF: com WP-CLI em PHP 8.3, modo --skip-plugins, restaurar opção anterior conforme studio-g5-option-rollback-20261117T123246Z (zero/ausente); rollback de código pelo backup privado respectivo. Nunca reativar limpeza sem teste.
- PR #314 permanece DRAFT até completar matriz G4 e reconciliação governada para branch canônica, embora arquivos aprovados já estejam instalados no servidor.

## G4 — Ampliação da homologação após ativação G5, execução 17/11 12:43 UTC
- [GitHub Actions #44085411557](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44085411557) — sucesso com os blobs GitHub integrados 4/4, incluindo o PHP de aprovação atualizado `16f5c014...`.
- Reexecutou 12 pares visuais de 0/1/N projetos em 1440×900/390×844, modo claro/escuro: `G4_VISUAL_BASELINE_PASS=1`.
- Cinco entradas globais e sete grupos internos testados no browser: `G6_NAV_VISUAL_5_AND_7=PASS`.
- C008 (parcial): navegação por 7 grupos, deep links, reload e back/forward com fragmento preservado: `G4_C008_G6_DEEP_LINK_HISTORY=PASS`. Persistência exata de rolagem ainda requer teste.
- C023 (parcial): sete grupos acessíveis no mobile 390 px, abrir manuscrito e ausência de overflow: `G4_C023_G6_MOBILE_NAV=PASS`. Drag, Quill e modais no mobile permanecem pendentes.
- C025 (parcial): página privada anônima retorna 403/404 sem título sintético do projeto; REST anônimo 401/403: `G4_C025_PRIVATE_REST_UNAUTH=PASS`. Cache-Control autenticado e integração com CDN ainda requerem revisão.
- Evidência: 26 screenshots sintéticas compactadas como artefato da execução; contêineres removidos.
- Estado de produção G5 já comprovado independentemente na execução #44084091092; nenhum projeto live foi modificado no ensaio.
