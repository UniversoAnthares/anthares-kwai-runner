# Kwai-up

Kwai-up e um publicador Android isolado dos pipelines atuais do `anthares-kwai-runner`.

## Objetivo

Reimplementar a sequencia nativa de publicacao comprovada no publicador historico `anthares-clipper/kwai_memu_publish.py`, removendo a dependencia de MEmu/MEMUC. O transporte e ADB generico e pode apontar para qualquer Android autorizado. O Xiaomi/Redmi do fluxo atual fica reservado para autenticacao; o executor de publicacao e um Android dedicado com sessao persistente.

## Contrato

1. Usa o app oficial `com.kwai.video`.
2. Exige `KWAI_UP_EXPECTED_ACCOUNT` e confirma a identidade pelo perfil antes de `prepare`.
3. Apaga somente arquivos proprios em `/sdcard/Movies/KwaiUp`.
4. Cada execucao cria um nome de midia deterministico com `job_id` e SHA-256.
5. O ledger recusa `job_id`, SHA-256 e intervalos de origem ja usados ou sobrepostos.
6. `prepare` chega a tela final e grava uma prova de prontidao; nenhum toque em Publicar ocorre nessa fase.
7. `commit` exige a prova de `prepare` e executa um unico toque em `com.kwai.video.basis:id/post`.
8. Sucesso exige evidencia posterior ao toque. Mensagens de revisao/pendencia ficam fora dos marcadores de sucesso.
9. Resultado `UNCERTAIN` permanece reservado no ledger e bloqueia repeticao do mesmo hash/intervalo.
10. Verificacao humana/CAPTCHA encerra a execucao em `FAILED_SAFE`.
11. Fila, lease, sessao e ledger dos sistemas atuais ficam isolados do Kwai-up.

## Entrada canonica para uma publicacao

```text
python3 kwai-up/kwai_up_job.py run
```

Variaveis obrigatorias do job:

```text
KWAI_UP_JOB_ID           identidade unica da entrega
KWAI_UP_SOURCE_ID        identidade canonica da live/video de origem
KWAI_UP_START_MS         inicio do trecho na origem
KWAI_UP_END_MS           fim do trecho na origem
KWAI_UP_MEDIA            caminho local do MP4
KWAI_UP_EXPECTED_ACCOUNT conta esperada, por exemplo lucasrosalem
```

Variaveis de transporte e seguranca:

```text
KWAI_UP_ADB_SERIAL       serial ADB opcional
KWAI_UP_MEDIA_SHA256     SHA-256 esperado; opcional, calculado quando ausente
KWAI_UP_CAPTION          legenda
KWAI_UP_LEDGER           padrao: .kwai-up/kwai-up.sqlite3
KWAI_UP_ARTIFACT_DIR     padrao: .kwai-up/artifacts
KWAI_UP_WAIT             espera base, padrao 8s
KWAI_UP_VERIFY_TIMEOUT   padrao 150s
```

Inspecao de um job reservado:

```text
python3 kwai-up/kwai_up_job.py show
```

Modos de diagnostico de baixo nivel:

```text
python3 kwai-up/kwai_up_safe.py probe
python3 kwai-up/kwai_up_safe.py auth
python3 kwai-up/kwai_up_safe.py prepare
python3 kwai-up/kwai_up_safe.py commit
python3 kwai-up/kwai_up_safe.py verify
```

## Sequencia nativa portada

- cold start por `am start -S --activity-clear-task`;
- confirmacao da conta esperada na UI do perfil;
- controle de criacao `com.kwai.video.basis:id/id_record_layout`;
- album nativo, aba `Videos`;
- item `com.kwai.video.basis:id/preview_container`;
- `com.kwai.video.ca_product:id/edit_next_button`;
- tela final `ShareActivity` com `com.kwai.video.basis:id/post`;
- captura da grade do perfil antes do commit;
- verificacao posterior por saida estrutural da ShareActivity, marcador textual estrito e insercao de novo card no perfil.

## Sessao

A primeira linhagem comprovada mantinha a conta dentro da VM Android persistente. O Kwai-up replica essa propriedade no executor dedicado: autentica uma vez, conserva a sessao do app no armazenamento persistente do Android e verifica a identidade antes de cada publicacao. O telefone fisico entra somente quando o Kwai exigir autenticacao ou aprovacao. Transferencia de `/data/user/0/com.kwai.video` exige root no Android de origem e destino; o telefone fisico comum fica fora desse mecanismo.

## Estado desta branch

A branch `kwai-up` e deliberadamente paralela e preserva os scripts atuais. A validacao de contrato executa 30 jobs simultaneos com variacoes de identidade, legenda, locale, serial ADB e casos de deduplicacao. Publicacao real permanece bloqueada ate existir um executor Android autenticado ligado ao transporte ADB desta nova camada.
