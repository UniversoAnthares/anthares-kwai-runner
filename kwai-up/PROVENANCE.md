# Kwai-up provenance

## Linha reconstruida

### Antes de MEmu

- 2026-09-25 a 2026-09-28: existiam corte, fila, claim, download e automacoes de YouTube. Nao ha evidencia de publicacao real no Kwai nesse periodo.
- 2026-09-29 23:31 -04:00 — commit `ed58654de795e0dd464a146752e2c746d965776f`, `Add Kwai Android UI publisher`. Surge `kwai_android_publish.py`, com ADB generico, app oficial `com.kwai.video`, envio do MP4 ao MediaStore e abertura por `android.intent.action.SEND`.
- 2026-09-30 00:10 -04:00 — commit `a2ba5508f34c4a6df69564d6d847e4d5db2f7aec`, `Run Kwai publisher on persistent Genymotion Android`. A ideia central de Android persistente aparece antes do MEmu.
- 2026-09-30 09:24 -04:00 — commit `61f2317ca2ba27a6e5dc4b73211e07c37838bc12`, `Add physical Android Kwai download and repost worker`, seguido do workflow self-hosted e de validacao do worker.
- 2026-10-01 14:02–14:10 -04:00 — essa familia e removida em uma serie de commits com mensagens `Remove obsolete...` e `Remove abandoned...`, incluindo o publicador Android UI, bootstrap persistente e phone worker. Os registros anteriores a essa remocao mostram construcao/probes; nao ha prova equivalente a insercao de card no perfil.
- 2026-10-01 20:15 -04:00 — commit `b78a4802a91fa7250258800bc428193c89d53220`, `Add local MEmu Kwai upload UI probe`. Comeca a linhagem que depois produz publicacao comprovada.

### Primeiro publicador MEmu

- 2026-10-02 03:08:56 UTC — commit `253be4b3d13bffc1f9fed599beae40161b606579`: `Add guarded Kwai MEmu publisher` em `UniversoAnthares/anthares-clipper`.
- O mecanismo usava o app oficial `com.kwai.video`, ADB e uma VM Android dedicada.
- O transporte especifico era MEMUC/MEmu; a logica de publicacao era Android nativa.
- A conta permanecia autenticada no armazenamento persistente da VM. O publicador assumia essa sessao pronta e operava a UI oficial.

### Sequencia que ficou comprovada

1. limpar a task salva do Kwai com `am start -S --activity-clear-task`;
2. esperar `com.kwai.video.basis:id/id_record_layout` na Home;
3. long-press no controle de criacao para abrir o Album do Kwai;
4. entrar em `Videos`;
5. exigir um unico `com.kwai.video.basis:id/preview_container` no executor dedicado;
6. selecionar o video;
7. tocar `com.kwai.video.ca_product:id/edit_next_button`;
8. exigir `ShareActivity`, campo `com.kwai.video.basis:id/editor` e `com.kwai.video.basis:id/post`;
9. tocar Publicar uma unica vez;
10. confirmar a saida estrutural da `ShareActivity` e uma segunda evidencia independente.

### Confirmacao real

- 2026-10-02 20:23:41 UTC — commit `fc458942eb1db93e25ab7f21eb9ae061ce1313df`: `Confirm Kwai publish by profile-grid insertion`.
- O publicador passou a fotografar a grade do perfil antes da publicacao e a confirmar que um novo card entrou na primeira linha depois da saida da `ShareActivity`.
- O marcador operacional de sucesso era `KWAI_MEMU_PUBLISH=OK` somente depois da confirmacao.
- A revisao anterior, commit `c7bd1e9a7e29adeb018f10198a36b4a92400b9c6`, ja separava confirmacao textual real de mensagens de pendencia/revisao.

### Publicacao continua

- 2026-10-03 20:53:59 UTC — commit `e6b855bd1124765436ee63debeaf5b069254ae79`: `Add continuous Kwai daily publisher daemon`.
- `kwai_daily_daemon.py` gerava cortes de 50 s via ffmpeg, chamava `kwai_memu_publish.py`, exigia retorno 0 + `KWAI_MEMU_PUBLISH=OK`, incrementava um ledger e seguia para o proximo corte.
- Essa e a primeira linhagem documentada em que publicacao real, repeticao automatica e confirmacao formavam um ciclo completo.

## Interpretacao do chat “Instrucoes para executor movel”

A referencia a uma “primeira versao” que ja conseguia fazer uploads sem Termux/Tailscale corresponde a essa linhagem Android nativa. Termux e Tailscale pertencem a uma proposta posterior de transformar um telefone em host/agente. Na linhagem comprovada, o executor era a VM MEmu controlada por ADB e a sessao persistia dentro dela. O celular fisico ficava fora do ciclo de publicacao.

## Decisao Kwai-up

Kwai-up recupera dois elementos antigos e conserva o que foi comprovado depois: transporte ADB generico, Android persistente, navegacao nativa mapeada por resource IDs, staging deterministico, separacao `prepare`/`commit`, prova da conta esperada e confirmacao por mudanca da grade do perfil. O Xiaomi/Redmi fica reservado para autenticacao/aprovacao. O executor de publicacao e um Android dedicado e controlavel, preservando o invariante de midia unica que tornou a selecao deterministica.
