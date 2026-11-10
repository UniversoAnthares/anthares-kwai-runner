# TikTok LIVE — cinco entradas web e Android 35 cloud com distribuição oficial
STATUS: PARTIAL
AREA: tiktok-live-standard-user-ui / tiktok-live-cloud-native-app
DATE: 2026-11-10
OWNER: chatgpt-tiktok-live-20261110-standard-user
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42870469378
JOB: 130020089274
COMMIT: 2740a229f723119cd8278c7dcf1d11084f990d63
SUPERSEDES: test-hub/findings/20261110-tiktok-live-standard-user-ui-route-running.md, test-hub/findings/20261110-tiktok-live-cloud-native-ui-running.md
LEASE_AREA: tiktok-live-standard-user-ui / tiktok-live-cloud-native-app
LEASE_STATUS: CLOSED

## Provas
- Browser padrão via sessão proprietária @lucasrosalem4, run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42868907327: cinco rotas oficiais, desktop profile, /live/creator, livecenter/producer, mobile profile, mobile live creator, HTTP 200. Todos NO_VISIBLE_GO_LIVE; produtor ofereceu download de LIVE Studio. Mobile profile mostrou login_form true.
- A plataforma Android nativa (Google Play API35 x86_64 no runner Ubuntu) iniciou e obteve TIKTOK_CLOUD_ANDROID_BOOT=READY no run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42869915635. O endereço TikTok https://www.tiktok.com/download-link/af/com.zhiliaoapp.musically devolveu HTTP 200 com corpo que não era APK ZIP, fim 42. Não houve instalação.
- Contorno permitido: fluxo padrão Google Play no Android virtual, run 42870469378 (job 130020089274): TIKTOK_CLOUD_ANDROID_BOOT=READY, TIKTOK_OFFICIAL_NATIVE_APK=UNAVAILABLE_USE_GOOGLE_PLAY, TIKTOK_GOOGLE_PLAY_LOGIN_REQUIRED=false, TIKTOK_GOOGLE_PLAY_INSTALL_CONTROL=false, TIKTOK_GOOGLE_PLAY=OFFICIAL_INSTALL_REQUIRES_ACCOUNT_OR_UNAVAILABLE. Esse sinal não prova que login Google está exigido: a tela não ofereceu opção detectada.
- Nenhuma identidade extra foi criada, nenhum token, cookie, chave RTMP ou pacote de terceiros foi utilizado. Nenhuma LIVE acionada; nenhuma rotina Kwai alterada.
- Testes anteriores de HLS Kwai + FFmpeg e câmera/microfone Chromium cloud seguem PROVEN, run 42853860337 e 42865993013.

## Consequência
Gravação LIVE no TikTok não está operacional. Falta um caminho oficial instalável/autenticado e autorizado para iniciar LIVE na conta, ou LIVE/RTMP habilitado na interface. Prerecorded stream deve ser identificado e cumprir políticas aplicáveis. Não recriar o mesmo teste sem correção causal (instalação via loja autenticada, APK oficial obtido de botão válido, ou liberação UI LIVE).
Preservar branch isolada PR #2301 draft, sem promoção, sem 24h cron ou broadcast duplicado.
