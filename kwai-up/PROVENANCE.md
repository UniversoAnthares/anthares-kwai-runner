# Kwai-up provenance

## Linha reconstruida

### Antes de MEmu

- 2026-09-25 a 2026-09-28: existiam corte, fila, claim, download e automacoes de YouTube. Nao existe evidencia de publicacao real no Kwai nesse periodo.
- 2026-10-01: os caminhos sem Android/MEmu ainda nao tinham produzido um video real no Kwai.

### Primeiro publicador nativo

- 2026-10-02 03:08:56 UTC — commit `253be4b3d13bffc1f9fed599beae40161b606579`: `Add guarded Kwai MEmu publisher` em `UniversoAnthares/anthares-clipper`.
- O mecanismo usava o app oficial `com.kwai.video`, ADB e uma VM Android dedicada.
- O transporte especifico era MEMUC/MEmu; a logica de publicacao era Android nativa.

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

### Publicacao continua

- 2026-10-03 20:53:59 UTC — commit `e6b855bd1124765436ee63debeaf5b069254ae79`: `Add continuous Kwai daily publisher daemon`.
- `kwai_daily_daemon.py` gerava cortes de 50 s via ffmpeg, chamava `kwai_memu_publish.py`, exigia retorno 0 + `KWAI_MEMU_PUBLISH=OK`, incrementava um ledger e seguia para o proximo corte.
- Essa e a primeira linhagem documentada em que publicacao real + repeticao automatica + confirmacao formavam um ciclo completo.

## Interpretacao do chat “Instrucoes para executor movel”

A referencia a uma “primeira versao” que ja conseguia fazer uploads sem Termux/Tailscale corresponde a essa linhagem Android nativa. O executor naquela fase era a VM MEmu controlada por ADB; o celular fisico nao era o executor de publicacao. Termux e Tailscale pertencem a uma proposta posterior de transformar um telefone em host/agente e nao faziam parte do mecanismo comprovado.

## Decisao Kwai-up

Kwai-up conserva a logica Android comprovada e substitui somente a camada MEmu/MEMUC por um transporte ADB generico. Autenticacao e publicacao sao componentes separados. O Xiaomi/Redmi pode permanecer apenas como origem de autenticacao; o executor de publicacao deve ser um Android dedicado e controlavel, preservando o invariante de midia unica que tornou a selecao deterministica.
