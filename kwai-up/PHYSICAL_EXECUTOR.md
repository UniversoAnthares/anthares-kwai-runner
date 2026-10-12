# Kwai-up — executor Android físico

## Estado comprovado em 2026-10-12

Executor validado: Redmi 9 / M2004J19C, Android SDK 31, Kwai Lite `kwai.lite.video`.

Contrato comprovado no aparelho real:

1. ADB alcança o aparelho por USB e por TCP/Wi-Fi.
2. `probe` retorna `PROBE_OK`.
3. `auth` confirma a identidade esperada antes de qualquer upload.
4. A mídia é copiada para `/sdcard/Movies/KwaiUp` com nome determinístico por job + SHA-256.
5. O Kwai Lite é aberto por `kwai://album` com `album_scroll_to_path` apontando para o arquivo exato.
6. Nós reciclados do álbum com bounds `[0,0][0,0]` são rejeitados.
7. A MIUI deste aparelho bloqueia `adb shell input`, Monkey e `UiAutomation.injectInputEvent` com `INJECT_EVENTS`; esses mecanismos não fazem parte do caminho operacional.
8. Os toques são enviados por um touchscreen HID temporário criado em `/dev/uhid`. O dispositivo HID é criado, usado para um toque e destruído imediatamente.
9. A seleção do vídeo foi comprovada até `com.yxcorp.gifshow.v3.EditorActivity`.
10. O botão `Próximo` foi comprovado até `com.yxcorp.gifshow.publish.ShareActivity`.
11. Na tela final foram confirmados o editor de legenda, privacidade `Público` e o controle `kwai.lite.video.basis:id/post`.
12. `prepare` foi comprovado no aparelho real terminando em `KWAI_UP_STATE=READY_TO_PUBLISH` sem tocar em `Publicar`.
13. Depois do teste, o app foi encerrado, `ready.json` de prova foi removido e as mídias de prova foram apagadas.

## Entradas operacionais

Diagnóstico/autenticação:

```bash
python kwai-up/kwai_up_physical_entry.py probe
python kwai-up/kwai_up_physical_entry.py auth
```

Job transacional real:

```bash
python kwai-up/kwai_up_physical_job.py run
```

Variáveis obrigatórias do job:

- `KWAI_UP_ADB_SERIAL`: endpoint ADB do aparelho; preferir TCP/Wi-Fi quando disponível.
- `KWAI_UP_PACKAGE=kwai.lite.video`
- `KWAI_UP_EXPECTED_ACCOUNT`: identidade exata esperada no perfil.
- `KWAI_UP_JOB_ID`
- `KWAI_UP_SOURCE_ID`
- `KWAI_UP_START_MS`
- `KWAI_UP_END_MS`
- `KWAI_UP_MEDIA`
- `KWAI_UP_CAPTION`: por enquanto deve ficar vazio no executor físico; legenda ainda permanece fail-closed até um caminho de texto ser validado.

## Segurança

`prepare` e `commit` permanecem separados. `prepare` pode chegar à tela final e criar a prova `READY_TO_PUBLISH`, mas não deve acionar o controle de publicação. `commit` é a única fronteira irreversível e só deve executar com prova `ready.json` válida para o mesmo job/mídia/legenda.

O ledger continua reservando job ID, SHA-256 e intervalo da fonte. Depois de iniciado `commit`, um resultado ambíguo permanece reservado como `UNCERTAIN` para impedir repetição automática do mesmo trecho.

## Bloqueio de tela

A sessão do Kwai persiste no aparelho. O PIN do Android não é contornado. Depois de reinicialização ou de um bloqueio seguro que exija credencial, a autenticação humana pode ser necessária. O sistema deve detectar a tela bloqueada e falhar de forma segura, nunca tentar adivinhar ou armazenar o PIN.
