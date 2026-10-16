# Fase 9 — redundância do Anthares Browser

STATUS: PROVEN
DATE: 2026-10-16

## Resultado

O Anthares Browser possui agora duas infraestruturas hospedadas independentes e elegíveis para executar a mesma prova canônica de runtime, sem Render, TinyFish, Browserless ou Cloudflare Browser Rendering.

### Primário — GitHub Actions público

- Workflow: `.github/workflows/anthares-brouser-runtime-qa40.yml`.
- Prova final usando o wrapper compartilhado `ci/shared/anthares-browser-runtime-proof.sh`.
- Run 38841592885: SUCCESS.
- A prova cobre health/readiness fail-closed, autenticação da API de controle, CDP apenas loopback, navegação, click, type, wait, evaluate, screenshot, noVNC, Chromium em execução e persistência do perfil após restart gracioso.

### Secundário independente — AppVeyor Linux

- Commit homologado: `66718568e1f0e799e3d9f8348a8d0efedc192c05`.
- Projeto `anthares-kwai-runner`, build 54907970 / 1.0.425: SUCCESS.
- Job Linux `bw7eb3k0ts0d94c3`: SUCCESS.
- Evidência do log: `ANTHARES_BROWSER_QA_PROVIDER=appveyor`, `ALL_3_CASES=PASS`, `HEALTH_LIVENESS=PASS`, `READY_FAIL_CLOSED=PASS`, `CONTROL_API_AUTH=PASS`, `CDP_LOOPBACK_ONLY=PASS`, `NAVIGATE=PASS`, `CLICK=PASS`, `TYPE=PASS`, `WAIT=PASS`, `EVALUATE=PASS`, `SCREENSHOT=PASS`, `NOVNC_ENDPOINT=PASS`, `CHROMIUM_RUNNING=PASS`, `PERSISTENT_BROWSER_PROFILE_RESTART=PASS`.
- O projeto duplicado `anthares-kwai-runner-1w7dq`, build 54907971 / 1.0.423, reproduziu a mesma prova com SUCCESS no job Linux `w4g7x7ylrp9atulw`. Isso é evidência repetida, não uma terceira redundância independente.

## Correções realizadas durante a homologação

- O restart de persistência da suíte passou a usar encerramento gracioso do container/Chromium antes de recriar o runtime com o mesmo volume.
- O AppVeyor passou de `clone_depth: 1` para `clone_depth: 50`, evitando `fatal: unable to read tree` quando `main` avança enquanto um build aguarda na fila.
- O wrapper `ci/shared/anthares-browser-runtime-proof.sh` passou a ser a prova rápida compartilhada entre provedores; a suíte profunda de 40 casos permanece disponível separadamente.

## Roteamento canônico

1. Superfície exclusiva: Anthares Browser.
2. Backend primário hospedado: GitHub Actions público Chromium.
3. Backend secundário independente: AppVeyor Linux Chromium.
4. Northflank permanece fora da seleção de browser até prova fresca de Chromium/persistência.
5. Render, TinyFish, Browserless e Cloudflare Browser Rendering permanecem inelegíveis.

## Conclusão

Fase 9 encerrada. A redundância está comprovada em dois provedores independentes executando o mesmo runtime/prova canônica.