# Item 1 — vincular instalação Appium a arquivos realmente verificados
STATUS: RUNNING
AREA: android|kwai
DATE: 2026-11-14
RUN: none
JOB: preparação da revisão do PR #2616
COMMIT: base fa7d7f4d236a8cc1c2858043bb30747984ba6970
SUPERSEDES: none
OWNER: ChatGPT item1 branch feature/spawndroid-kwai-apk-verified-upload-20261114
GOVERNANCE_RULES_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138

## BASELINE_PROVEN
- ARA verificação somente leitura de 25/25 arquivos com.kwai.video e 18/18 arquivos kwai.lite.video: tamanho e SHA256 coincidindo com os manifestos locais, 0 divergências. Source local no Anthares, sem staging novo.
- GitHub Actions PR #2616 execução 43622425772: 16+20 testes offline verdes; sem teste Appium real. `cloud_cutover.enabled=false`.
- API SpawnDroid exige app artifact previamente cadastrado para provisionar sessão. Appium UiAutomator2 declara `mobile: installMultipleApks` com `apks: Array<string>`, opções `timeout`, `replace`.
- Gap de segurança: `webdriver_script` hoje aceita URLs em texto sem exigir manifestos e bytes efetivamente auditados; um executor mal configurado poderia instalar fontes arbitrárias se canary gate estivesse habilitado.

## FAILED_AVOIDED
Evitar chamada real de Appium sem hash/assinatura verificados em runner cloud; nenhuma nova sessão cloud, nenhum reempacotamento/reassinatura, sem alterar publicadores, não repetir HTTP403 de APKMirror.

## SUCCESS_SIGNAL
`webdriver_script` exige manifesto com host HTTPS permitido, todas as URLs iguais às declaradas, diretório efêmero de runner GitHub, assinatura v2/v3, pacote/versão e hashes auditados para TODOS os splits antes da primeira chamada Appium. Testes em CI rejeitam troca de URL, manifesto sem dados, ausência de prova cloud, mudança de versão e pacote.

## FAILURE_SIGNAL
Qualquer método WebDriver iniciado antes de validação de manifestos e arquivos; falha CI; conflito com outro agente, mudança não reconciliada de branch ou peer.

## TEST_VALIDITY
Offline unit contracts, com mocks. Ainda requer transferir os splits originais via armazenamento privado HTTPS, sessão Appium legítima já provisionada, comprovação do driver do SpawnDroid e encerramento, sem mudanças de roteamento de produção.

## LEASE
Escopo exclusivo de modificação: `tools/kwai_spawndroid_original_splits.py`, `tests/test_kwai_spawndroid_original_splits.py`, `test-hub/findings/20261114-item1-appium-install-source-binding-*.md` na branch própria de PR #2616. GitLab main lido e sem arquivo homônimo; nenhuma sincronização cross-provider.
