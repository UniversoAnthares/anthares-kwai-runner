# Kwai-up

Kwai-up e um publicador Android isolado dos pipelines atuais do `anthares-kwai-runner`.

## Objetivo

Reimplementar a sequencia nativa de publicacao que foi comprovada no publicador historico `anthares-clipper/kwai_memu_publish.py`, removendo a dependencia de MEmu/MEMUC. O transporte e ADB generico e pode apontar para qualquer Android autorizado. O Xiaomi/Redmi usado no fluxo atual permanece destinado a autenticacao; o publicador e uma camada separada.

## Contrato

1. Usa o app oficial `com.kwai.video`.
2. Nunca apaga videos fora de `/sdcard/Movies/KwaiUp`.
3. Cada execucao cria um nome de midia deterministico com `job_id` e SHA-256.
4. `prepare` leva a execucao ate a tela final e grava uma prova de prontidao; nenhum toque em Publicar ocorre nessa fase.
5. `commit` exige a prova produzida por `prepare` e executa um unico toque no controle nativo `com.kwai.video.basis:id/post`.
6. Sucesso exige evidencia posterior ao toque. O estado final e `VERIFIED`, `UNCERTAIN` ou `FAILED_SAFE`.
7. Verificacao humana/CAPTCHA encerra a execucao em `FAILED_SAFE`.
8. Nenhuma fila, lease, sessao ou ledger dos sistemas atuais e alterada.

## Modos

```text
python3 kwai-up/kwai_up.py probe
python3 kwai-up/kwai_up.py prepare
python3 kwai-up/kwai_up.py commit
python3 kwai-up/kwai_up.py verify
```

Variaveis principais:

```text
KWAI_UP_ADB_SERIAL       serial ADB opcional
KWAI_UP_MEDIA            caminho local do MP4
KWAI_UP_JOB_ID           identidade da entrega
KWAI_UP_MEDIA_SHA256     SHA-256 esperado; opcional, calculado quando ausente
KWAI_UP_CAPTION          legenda
KWAI_UP_ARTIFACT_DIR     padrao: .kwai-up/artifacts
KWAI_UP_WAIT             espera base, padrao 8s
KWAI_UP_VERIFY_TIMEOUT   padrao 150s
```

## Sequencia nativa portada

- cold start por `am start -S --activity-clear-task`;
- controle de criacao `com.kwai.video.basis:id/id_record_layout`;
- album nativo, aba `Videos`;
- item `com.kwai.video.basis:id/preview_container`;
- `com.kwai.video.ca_product:id/edit_next_button`;
- tela final `ShareActivity` com `com.kwai.video.basis:id/post`;
- captura do perfil antes do commit;
- verificacao posterior por saida estrutural da ShareActivity, marcador textual e mudanca da grade do perfil.

## Estado desta branch

A branch `kwai-up` e deliberadamente paralela. Ela nao altera os scripts de publicacao existentes. A validacao de contrato executa 30 jobs simultaneos com variacoes de identidade, legenda, locale e serial ADB. Publicacao real permanece bloqueada ate existir um Android autenticado ligado ao transporte ADB desta nova camada.
