# Android remoto Google Play v5 — janela interativa protegida e ativa
STATUS: PARTIAL
AREA: tiktok-live-cloud-google-remote-login
DATE: 2026-11-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42877031868
JOB: 130043365105
COMMIT: 498a59711de9483ecf0ab689c7b8e677b9262cb0
SUPERSEDES: test-hub/findings/20261110-android-google-remote-login-v5-running.md

## Evidência
- GitHub Ubuntu 24.04 instalou scrcpy v3.3.4 do release oficial, SHA-256 verificado; corrigiu incompatibilidade anterior do scrcpy 1.25.
- Android 35 Google Play e KVM/ADB foram inicializados e os passos concluíram com sucesso.
- A interface Xvfb/scrcpy/noVNC via Cloudflare Quick Tunnel verificou HTTP401 sem autorização e HTTP200 com autenticação.
- As credenciais temporárias da interface foram criadas aleatoriamente e criptografadas com RSA-OAEP/SHA256. GitHub Actions artifact id 13791079806 contém exclusivamente a cifra; o acesso foi descriptografado localmente e entregue ao titular somente pela conversa.
- A etapa Keep virtual Android and remote tunnel accessible estava em andamento na última consulta. O Google Play foi aberto no Android remoto.
- O teste preliminar 42875862044 falhou ao criar comentário de PR com erro HTTP403; novo fluxo entregou a cifra por artefato GitHub. A execução intermediária 42876956075 foi cancelada.

## Limite
A autenticação Google depende da ação do titular. Login Google, instalação do TikTok e LIVE aos espectadores ainda não estão comprovados. O emulador é efêmero e sua sessão precisa ser armazenada com criptografia para uso posterior. Nenhuma credencial Google foi capturada ou publicada.
