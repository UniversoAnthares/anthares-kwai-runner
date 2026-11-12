# Kwai CORTES — recuperação, reconciliação e callback de origem
STATUS: OPERACIONAL_COM_ACK_PUBLICO_PENDENTE
DATE: 2026-11-12 17:32 America/Campo_Grande
GOVERNANCE_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138
SCOPE: kwai:lucasrosalem; kwai:universoanthares

## Correções concluídas e evidências
1. **USB Redmi 9**: o dispositivo deixou de responder a `adb shell` e desapareceu dos servidores ADB. A interface PnP exata `USB\VID_18D1&PID_4EE7\993FCE720408` foi reiniciada. O comando PnP indicou que reinício do SO poderia ser necessário, porém o ADB voltou sem reinicializar Windows: `adb -P 5037 devices` identificou `993fce720408 M2004J19C`; `adb -P 5037 -s 993fce720408 shell echo ANTHARES_ADB_RESTORED` devolveu o texto correto. Preservar o perfil e as sessões.
2. **Preparação física**: mídia reusável no Android após comparar SHA-256, falha fechada se arquivo existente divergir; MediaStore só reindexado quando necessário. Timeout de abertura de editor resolvido removendo `am start -W`, mantendo conferência da UI antes de publicar. Testes e PR [#2449](https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2449), CI aprovado.
3. **Perfil secundário**: a janela opcional de notificações cobria a aba da conta `@universoanthares`. Fechamento permitido apenas para `com.kwai.video.basis:id/tv_dialog_title` com texto de notificações + exatamente um botão `com.kwai.video:id/iv_close` habilitado; variante Kwai Lite preservada; casos desconhecidos não recebem toque. Testes simulados de ambas as contas, [PR #2450](https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2450), CI aprovado.
4. **Prova pública independente**: produção Neon deployment 72 permitiu confirmação de duas contas com quatro quadros SIFT e SHA do clipe original, mesmo quando a legenda é opcional. Dedupe, conta, horário e URL exata continuam obrigatórios; [PR #2444](https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2444).
5. **Reconciliar e dispensar**: versão 71 adicionou listagem/confirm/cancel no servidor assinadas pelo executor físico, respeitando janelas de segurança. Reconciliar publicação por URL + autor + mídia; quando inconclusiva, cancelar definitivamente sem republicar e reter a identidade do corte; [PR #2443](https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2443).
6. **Callback WordPress**: Neon deployment 73, [PR #2453](https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2453), CI aprovado. Confirmações reconciliadas chamam a API CORTES usando token retido no backend e URL permitida `anthares.us`. Falha mantém pendência idempotente, jamais reenvia o vídeo. O daemon operacional procura callbacks pendentes a cada 10 minutos. Hotfix local `tools/kwai_physical_queue_daemon.py` SHA256 `064ACF1D888F8F9E243D23A1FC678DC3B8C728AA52BE60FF99EE91C246C0E5CE`, verificado por teste de ordem `wp-sync` antes de `list` sem Android. Os dois daemons foram reiniciados pelo agendador, PIDs 23852 e 27004 às 17:32.
7. **Duas reconciliações adicionais com confirmação WordPress**:
   - primária `cOhqEaY3-08:706–748`: `https://www.kwai.com/@lucasrosalem/video/5249095477377875436`, source SHA `83c0585a6bdde2de64a780cbb696a20a9993093af41df1070fecd7973c3eee73`, quatro quadros `[254,211,310,303]`, status `confirmed`, `wp_callback_state=completed`.
   - secundária `ua-767b60e6`: `https://www.kwai.com/@universoanthares/video/5201807682365205591`, source SHA `d88cac09c49e9003d8ca6bb7e31525936632255bf1fc7045d431ec54fed8f4e7`, quatro quadros `[289,315,282,234]`, status `confirmed`, `wp_callback_state=completed`.
8. **Cadência**: fonte central Neon continua `kwai-public-post-proportional-v2` para as duas contas, limite 100/dia e distribuição proporcional até 23h, com trava antes de novos leases.

## Snapshot de 17:32 (-04), 12/11/2026
- `kwai:lucasrosalem`: 562 confirmed, 50 queued, 1 started/ACK público pendente, 14 failed históricos, 1 cancelled, 0 uncertain.
- `kwai:universoanthares`: 20 confirmed, 68 queued, 1 started/ACK público pendente, 1 failed histórico, 4 cancelled, 0 uncertain.
- Dois ACKs aguardavam indexação/prova pública (primária corte 872–914; secundária `ua-8710c357`); o daemon bloqueia novas leases na mesma conta enquanto há `published_pending_ack`. Nunca forçar confirmação sem prova ou reenviar o corte incerto.
- O arquivo `tools/kwai_physical_queue_daemon.py` **operacional no Windows diverge da versão legada do mesmo caminho na árvore central**; preservar hotfix e trabalho concorrente ao sincronizar. Este registro não implica equivalência do arquivo legado.
- Nenhum vídeo ou mídia novo foi usado como armazenamento permanente no PC; mídia e provas em fluxo, logs e estados de controle existentes.

## Pendências remanescentes
- Provar os dois últimos vídeos ou registrar descarte segundo a política vigente após janelas de propagação do perfil.
- Acompanhar os próximos ACKs para confirmar que todos chegam a `confirmed` e ao callback da origem, com intervalos até 23h.
- Sincronizar com cautela o daemon operacional Windows e o repositório central quando versões concorrentes forem conciliadas. Não substituir o executável funcional pelo legado sem diff e testes.
